from tqdm import tqdm
import zipfile
import sys
import random
import time

from dbmodel import *


JSON_TYPE_TOP_OBJECT = 1  # top level object
JSON_TYPE_TOP_NEXT = 2  # top level array
JSON_TYPE_ENTRY = 3  # object in top level array
JSON_TYPE_ENTRY_VALUE = 4  # objects, arrays, values in object in top level array
JSON_TYPE_ENTRY_VALUE_ENTRY = 5


def convert_to_dt(s):
    if not isinstance(s, int):
        if s is None or s.lower() == 'none':
            return None
        if isinstance(s, str):
            if s.startswith('TMSTMP-') is True:
                s = s.replace('TMSTMP-', '')
            elif s == 'Never':
                s = -1
        try:
            s = int(s)
        except:
            # logger.debug('Datetime conversion failed for value %s' % s)
            return None
    return datetime.datetime.utcfromtimestamp(s)


def rando():
    min_ = 2147483647
    max_ = 4294967295
    rand = random.randint(min_, max_)
    return rand


def read_file_chunk(f, block_size=65535):
    try:
        return f.read(block_size)
    except Exception as ex:
        return ''


class Importer:
    def __init__(self, db_conn=None, db_session=None):
        self.debug = False
        self.json_files = []
        self.db_conn = db_conn
        self.db_session = db_session
        self.json_parser = JsonParser(self)
        self.gi = None

        self.ads = {}  # sid -> ad_id
        self.adn = {}  # name -> ad_id

        random.seed(time.time())

    def setup_db(self):
        if self.db_session is None:
            self.db_session = get_session(self.db_conn)

    def get_adid_by_name(self, name):
        if name in self.adn:
            return self.adn[name]
        else:
            q = self.db_session.query(Domain).filter_by(name=name).first()
            if q:
                return q.id
        return None

    def get_adid_by_sid(self, sid):
        if sid in self.ads:
            return self.ads[sid]
        else:
            q = self.db_session.query(Domain).filter_by(objectSid=sid).first()
            if q:
                return q.id
        return None

    def sid_to_id(self, sid, adid, objtype='unknown'):
        """ Retreive database for object base on object id """
        res = self.db_session.query(EdgeLookup).filter_by(oid=sid).filter(EdgeLookup.ad_id == adid).first()
        if res:
            return res.id
        else:
            edgeinfo = EdgeLookup(adid, sid, objtype)
            self.db_session.add(edgeinfo)
            self.db_session.commit()
            self.db_session.refresh(edgeinfo)
            return edgeinfo.id

    def json_handler(self, json_type, bh_version, entries):
        if bh_version == 4 or bh_version == 3:
            if json_type == 'domains':
                self.import_domain_v4(bh_version, entries)
            elif json_type == 'gpos':
                self.import_gpo_v4(bh_version, entries)
            elif json_type == 'ous':
                self.import_ou_v4(bh_version, entries)
            elif json_type == 'containers':
                self.import_container_v4(bh_version, entries)
            elif json_type == 'groups':
                self.import_group_v4(bh_version, entries)
            elif json_type == 'computers':
                self.import_machine_v4(bh_version, entries)
            elif json_type == 'users':
                self.import_user_v4(bh_version, entries)
            else:
                print('Unsupported collection type', json_type)
                input()
        else:
            pass
            # print(f'Unsupported bloodhound version {bh_version}')

    def add_aces(self, bh_version, ad_id, objectid, aces):
        """ Import ACEs dict (from json parsing) to database """
        for _, ace in aces.items():
            values = ace['values']
            dst = values['PrincipalSID']
            dst_type = values['PrincipalType']
            if bh_version == 3:
                if values['RightName'] == 'ExtendedRight' or values['RightName'] == 'WriteProperty':
                    label = values['AceType']
                else:
                    label = values['RightName']
            else:
                label = values['RightName']
            newace = Ace(ad_id, objectid, dst, dst_type, label)
            self.db_session.add(newace)

    def import_domain_v4(self, bh_version, entries):
        """ Import BloodHound Domain JSON data to database """
        objects = entries['objects']
        arrays = entries['arrays']
        values = entries['values']

        # isaclprotected = values['IsACLProtected']
        # isdeleted = values['IsDeleted']
        objectid = values['ObjectIdentifier']

        di = Domain()

        if 'Properties' in objects.keys():
            values = objects['Properties']['values']
            di.name = values['name']
            di.objectSid = objectid
            di.distinguishedName = values['distinguishedname']
            if 'whencreated' in values:
                di.whenCreated = convert_to_dt(values['whencreated'])
            # skipped Properties: domain, description, functionallevel

        # di.gen_checksum()

        self.db_session.add(di)
        self.db_session.commit()
        self.db_session.refresh(di)

        edgeinfo = EdgeLookup(di.id, objectid, 'domain')
        self.db_session.add(edgeinfo)
        self.db_session.commit()

        self.ads[objectid] = di.id
        self.adn[di.name] = di.id

        # add aces to global Ace table (these will be turned into edges later)
        if 'Aces' in arrays.keys():
            if len(arrays['Aces']) > 0:
                self.add_aces(bh_version, di.id, objectid, arrays['Aces']['objects'])

        # skipped: ChildObjects
        # TODO: Trusts, Links

        self.db_session.commit()

    def import_group_v4(self, bh_version, entries):
        """ Import BloodHound Group JSON data to database """
        try:
            objects = entries['objects']
            arrays = entries['arrays']
            values = entries['values']

            if 'ObjectIdentifier' not in values:
                print('import_group_v4, no objectidentifier', entries)
                return

            # isaclprotected = values['IsACLProtected']
            # isdeleted = values['IsDeleted']
            objectid = values['ObjectIdentifier']

            # if objectid == 'S-1-5-21-3937601378-3721788405-2067139823-512':
            #    print('HERE!!', arrays)
            #    input()

            m = Group()

            if 'Properties' in objects.keys():
                values = objects['Properties']['values']

                if 'domainsid' in values:
                    m.ad_id = self.get_adid_by_sid(values['domainsid'])
                elif 'domain' in values:
                    m.ad_id = self.get_adid_by_name(values['domain'])

                if m.ad_id is None:
                    # TODO...unknown domain??? trusts maybe
                    return

                m.name = values['name'].split('@', 1)[0]
                m.sAMAccountName = m.name
                m.cn = m.name
                m.objectSid = objectid

                if 'description' in values and values['description']:
                    m.description = values['description']
                if 'distinguishedname' in values and values['distinguishedname']:
                    m.dn = values['distinguishedname']
                if 'admincount' in values:
                    m.adminCount = values['admincount']
                if 'whencreated' in values:
                    m.whenCreated = convert_to_dt(values['whencreated'])
            # m.gen_checksum()

            self.db_session.add(m)
            edgeinfo = EdgeLookup(m.ad_id, objectid, 'group')
            self.db_session.add(edgeinfo)

            if 'Members' in arrays.keys():
                if len(arrays['Members']) > 0:
                    members = arrays['Members']['objects']
                    for _, member in members.items():
                        values = member['values']
                        if bh_version == 4:
                            member_sid = values['ObjectIdentifier']
                            member_type = values['ObjectType']
                            newmember = Member(m.ad_id, objectid, member_sid, member_type)
                            self.db_session.add(newmember)
                        elif bh_version == 3:
                            member_sid = values['MemberId']
                            member_type = values['MemberType']
                            newmember = Member(m.ad_id, objectid, member_sid, member_type)
                            self.db_session.add(newmember)

            # add aces to global Ace table (these will be turned into edges later)
            if 'Aces' in arrays.keys():
                if len(arrays['Aces']) > 0:
                    self.add_aces(bh_version, m.ad_id, objectid, arrays['Aces']['objects'])

            self.db_session.commit()
        except Exception as ex:
            print('import_group_v4', ex)

    def import_user_v4(self, bh_version, entries):
        """ Import BloodHound User JSON data to database """
        try:
            objects = entries['objects']
            arrays = entries['arrays']
            values = entries['values']

            if 'ObjectIdentifier' not in values:
                print('import_user_v4, no objectidentifier', entries)
                return

            # isaclprotected = values['IsACLProtected']
            # isdeleted = values['IsDeleted']
            objectid = values['ObjectIdentifier']
            # primarygroupsid = values['PrimaryGroupSID']

            m = User()
            if 'Properties' in objects.keys():
                values = objects['Properties']['values']

                if 'domainsid' in values:
                    m.ad_id = self.get_adid_by_sid(values['domainsid'])
                elif 'domain' in values:
                    m.ad_id = self.get_adid_by_name(values['domain'])

                if m.ad_id is None:
                    # TODO...unknown domain??? trusts maybe
                    return

                m.name = values['name'].split('@', 1)[0]
                m.cn = m.name
                m.sAMAccountName = m.name
                m.objectSid = objectid
                if 'distinguishedname' in values and values['distinguishedname']:
                    m.dn = values['distinguishedname']
                if 'description' in values and values['description']:
                    m.description = values['description']
                if 'displayname' in values and values['displayname']:
                    m.displayName = values['displayname']
                if 'email' in values and values['email']:
                    m.email = values['email']
                if 'dontreqpreauth' in values:
                    m.UAC_DONT_REQUIRE_PREAUTH = values['dontreqpreauth']
                if 'passwordnotreqd' in values:
                    m.UAC_PASSWD_NOTREQD = values['passwordnotreqd']
                if 'unconstraineddelegation' in values:
                    m.UAC_TRUSTED_FOR_DELEGATION = values['unconstraineddelegation']
                if 'enabled' in values:
                    m.canLogon = values['enabled']
                if 'pwdneverexpires' in values:
                    m.UAC_DONT_EXPIRE_PASSWD = values['pwdneverexpires']
                if 'admincount' in values:
                    m.adminCount = values['admincount']
                if 'pwdlastset' in values:
                    m.pwdLastSet = convert_to_dt(values['pwdlastset'])
                if 'lastlogontimestamp' in values:
                    m.lastLogonTimestamp = convert_to_dt(values['lastlogontimestamp'])
                if 'lastlogon' in values:
                    m.lastLogon = convert_to_dt(values['lastlogon'])
                if 'whencreated' in values:
                    m.whenCreated = convert_to_dt(values['whencreated'])

                prop_arrays = objects['Properties']['arrays']
                if 'serviceprincipalnames' in prop_arrays and 'values' in prop_arrays['serviceprincipalnames']:
                    values = prop_arrays['serviceprincipalnames']['values']
                    for _, spn_str in values.items():
                        if len(spn_str) > 0:
                            if m.servicePrincipalName is None or len(m.servicePrincipalName) == 0:
                                m.servicePrincipalName = spn_str
                            else:
                                m.servicePrincipalName = m.servicePrincipalName + '|' + spn_str
                            new_spn = UserSPN.from_spn_str(spn_str, m.objectSid)
                            new_spn.ad_id = m.ad_id
                            self.db_session.add(new_spn)

                # Skipping properties: sensitive, trustedtoauth, hasspn, title, homedirectory, userpassword
                # unixpassword, unicodepassword, sfupassword, sidhistory
            # m.gen_checksum()

            self.db_session.add(m)
            edgeinfo = EdgeLookup(m.ad_id, objectid, 'user')
            self.db_session.add(edgeinfo)

            # add aces to global Ace table (these will be turned into edges later)
            if 'Aces' in arrays.keys():
                if len(arrays['Aces']) > 0:
                    self.add_aces(bh_version, m.ad_id, objectid, arrays['Aces']['objects'])

            self.db_session.commit()
        except Exception as ex:
            print('import_user_v4', ex)

    def import_machine_v4(self, bh_version, entries):
        """ Import BloodHound Computer JSON data to database """
        try:
            objects = entries['objects']
            arrays = entries['arrays']
            values = entries['values']

            # isaclprotected = values['IsACLProtected']
            # isdeleted = values['IsDeleted']
            if 'ObjectIdentifier' in values:
                objectid = values['ObjectIdentifier']
            else:
                objectid = ''
            # status = values['Status']
            if 'PrimaryGroupSID' in values:
                primarygroupsid = values['PrimaryGroupSID']
            else:
                primarygroupsid = None

            m = Computer()
            if 'Properties' in objects.keys():
                values = objects['Properties']['values']

                if 'domainsid' in values:
                    m.ad_id = self.get_adid_by_sid(values['domainsid'])
                elif 'domain' in values:
                    m.ad_id = self.get_adid_by_name(values['domain'])

                if m.ad_id is None:
                    # TODO...unknown domain??? trusts maybe
                    return

                m.name = values['name'].split('.', 1)[0]
                m.displayName = m.name
                m.dn = values['distinguishedname']
                m.canLogon = values['enabled']
                m.lastLogonTimestamp = convert_to_dt(values['lastlogontimestamp'])
                m.pwdLastSet = convert_to_dt(values['pwdlastset'])
                m.dNSHostName = values['name']
                m.cn = values['name'].split('.', 1)[0]
                m.sAMAccountName = m.name + '$'
                if len(objectid) == 0:
                    objectid = values['objectid']
                m.objectSid = objectid
                m.UAC_TRUSTED_FOR_DELEGATION = values['unconstraineddelegation']
                if primarygroupsid:
                    m.primaryGroupID = primarygroupsid.split('-')[-1]
                if 'description' in values and values['description']:
                    m.description = values['description']
                if 'operatingsystem' in values and values['operatingsystem']:
                    m.operatingSystem = values['operatingsystem']
                if 'whencreated' in values:
                    m.whenCreated = convert_to_dt(values['whencreated'])

                prop_arrays = objects['Properties']['arrays']
                if 'serviceprincipalnames' in prop_arrays and 'values' in prop_arrays['serviceprincipalnames']:
                    values = prop_arrays['serviceprincipalnames']['values']
                    for _, spn_str in values.items():
                        if len(spn_str) > 0:
                            if m.servicePrincipalName is None or len(m.servicePrincipalName) == 0:
                                m.servicePrincipalName = spn_str
                            else:
                                m.servicePrincipalName = m.servicePrincipalName + '|' + spn_str
                            new_spn = ServiceSPN.from_spn_str(spn_str, m.objectSid)
                            new_spn.ad_id = m.ad_id
                            self.db_session.add(new_spn)

                # Skipping properties: haslaps, trustedtoauth, lastlogon, sidhistory
            else:
                # in some cases there is no property block...guess pass on those
                return

            if 'Sessions' in objects.keys():
                values = objects['Sessions']['values']
                if 'Collected' in values and values['Collected'] is True:
                    print('Session data...not supported yet')

            if 'LocalAdmins' in objects.keys():
                values = objects['Sessions']['values']
                if 'Collected' in values and values['Collected'] is True:
                    print('LocalAdmins data...not supported yet')

            if 'RemoteDesktopUsers' in objects.keys():
                values = objects['RemoteDesktopUsers']['values']
                if 'Collected' in values and values['Collected'] is True:
                    print('RemoteDesktopUsers data...not supported yet')

            if 'DcomUsers' in objects.keys():
                values = objects['DcomUsers']['values']
                if 'Collected' in values and values['Collected'] is True:
                    print('DcomUsers data...not supported yet')

            if 'PSRemoteUsers' in objects.keys():
                values = objects['PSRemoteUsers']['values']
                if 'Collected' in values and values['Collected'] is True:
                    print('PSRemoteUsers data...not supported yet')

            # add new machine to database
            # m.gen_checksum()
            self.db_session.add(m)

            # create objectid to id lookup entry
            edgeinfo = EdgeLookup(m.ad_id, objectid, 'machine')
            self.db_session.add(edgeinfo)

            # add aces to global Ace table (these will be turned into edges later)
            if 'Aces' in arrays.keys():
                if len(arrays['Aces']) > 0:
                    self.add_aces(bh_version, m.ad_id, objectid, arrays['Aces']['objects'])

            if bh_version == 3:
                if 'LocalAdmins' in arrays.keys():
                    if len(arrays['LocalAdmins']) > 0:
                        print('Not supported yet', arrays['LocalAdmins']['values'])

                if 'RemoteDesktopUsers' in arrays.keys():
                    if len(arrays['RemoteDesktopUsers']) > 0:
                        print('Not supported yet', arrays['RemoteDesktopUsers']['values'])

                if 'Sessions' in arrays.keys():
                    if len(arrays['Sessions']) > 0:
                        print('Not supported yet', arrays['Sessions']['values'])

            self.db_session.commit()
        except Exception as ex:
            print('import_machine_v4', ex)

    def import_gpo_v4(self, bh_version, entries):
        """ Import BloodHound GPO JSON data to database """
        try:
            objects = entries['objects']
            arrays = entries['arrays']
            values = entries['values']

            if 'ObjectIdentifier' not in values:
                return

            # isaclprotected = values['IsACLProtected']
            # isdeleted = values['IsDeleted']
            objectid = values['ObjectIdentifier']

            m = GPO()
            if 'Properties' in objects.keys():
                values = objects['Properties']['values']

                if 'domainsid' in values:
                    m.ad_id = self.get_adid_by_sid(values['domainsid'])
                elif 'domain' in values:
                    m.ad_id = self.get_adid_by_name(values['domain'])

                if m.ad_id is None:
                    # TODO...unknown domain??? trusts maybe
                    return

                m.name = values['name'].split('@', 1)[0]
                m.objectGUID = objectid
                if values['description']:
                    m.description = values['description']
                if 'distinguishedname' in values and values['distinguishedname']:
                    m.dn = values['distinguishedname']
                    m.cn = m.dn.split(',')[0].strip('CN=')
                if values['gpcpath']:
                    m.path = values['gpcpath']
                if 'whencreated' in values:
                    m.whenCreated = convert_to_dt(values['whencreated'])
            # m.gen_checksum()

            self.db_session.add(m)
            edgeinfo = EdgeLookup(m.ad_id, objectid, 'gpo')
            self.db_session.add(edgeinfo)
            self.db_session.commit()

            # add aces to global Ace table (these will be turned into edges later)
            if 'Aces' in arrays.keys():
                if len(arrays['Aces']) > 0:
                    self.add_aces(bh_version, m.ad_id, objectid, arrays['Aces']['objects'])

            self.db_session.commit()
        except Exception as ex:
            print('import_gpo_v4', ex)

    def import_ou_v4(self, bh_version, entries):
        """ Import BloodHound OU JSON data to database """
        try:
            objects = entries['objects']
            arrays = entries['arrays']
            values = entries['values']

            if 'ObjectIdentifier' not in values:
                return

            # isaclprotected = values['IsACLProtected']
            # isdeleted = values['IsDeleted']
            objectid = values['ObjectIdentifier']

            m = Ou()

            if 'Properties' in objects.keys():
                prop_values = objects['Properties']['values']

                if 'domainsid' in prop_values:
                    m.ad_id = self.get_adid_by_sid(prop_values['domainsid'])
                elif 'domain' in prop_values:
                    m.ad_id = self.get_adid_by_name(prop_values['domain'])

                if m.ad_id is None:
                    # TODO...unknown domain??? trusts maybe
                    return

                m.name = prop_values['name'].split('@', 1)[0]
                m.ou = m.name
                m.objectGUID = objectid
                if prop_values['description']:
                    m.description = prop_values['description']
                if prop_values['distinguishedname']:
                    m.dn = prop_values['distinguishedname']
                if 'whencreated' in prop_values:
                    m.whenCreated = convert_to_dt(prop_values['whencreated'])

            self.db_session.add(m)
            edgeinfo = EdgeLookup(m.ad_id, objectid, 'ou')
            self.db_session.add(edgeinfo)
            self.db_session.commit()

            # add aces to global Ace table (these will be turned into edges later)
            if 'Aces' in arrays.keys():
                if len(arrays['Aces']) > 0:
                    self.add_aces(bh_version, m.ad_id, objectid, arrays['Aces']['objects'])

            if 'Links' in arrays.keys():
                if len(arrays['Links']) > 0:
                    links = arrays['Links']['objects']
                    for _, link in links.items():
                        link_values = link['values']
                        if bh_version == 4:
                            if 'ObjectIdentifier' in link_values:  # TODO maybe remove this
                                gpo_guid = link_values['ObjectIdentifier']
                            elif 'GUID' in link_values:
                                gpo_guid = link_values['GUID']
                            else:
                                continue
                            newgplink = Gplink(m.ad_id, objectid, gpo_guid)
                            self.db_session.add(newgplink)
                        elif bh_version == 3:
                            gpo_guid = link_values['Guid']
                            newgplink = Gplink(m.ad_id, objectid, gpo_guid)
                            self.db_session.add(newgplink)

            if 'ChildObjects' in arrays.keys():
                if len(arrays['ChildObjects']) > 0:
                    childobjects = arrays['ChildObjects']['objects']
                    for _, child in childobjects.items():
                        child_values = child['values']
                        if bh_version == 4:
                            child_id = child_values['ObjectIdentifier']
                            child_type = child_values['ObjectType']
                            newchild = ChildObject(m.ad_id, objectid, child_id, child_type)
                            self.db_session.add(newchild)

            if bh_version == 3:
                # childobjects stored in Users, Computers, childous (just a list of sides)
                if 'Users' in arrays.keys():
                    if len(arrays['Users']) > 0:
                        childobjects = arrays['Users']['values']
                        for _, child_id in childobjects.items():
                            newchild = ChildObject(m.ad_id, objectid, child_id, 'User')
                            self.db_session.add(newchild)

                if 'Computers' in arrays.keys():
                    if len(arrays['Computers']) > 0:
                        childobjects = arrays['Computers']['values']
                        for _, child_id in childobjects.items():
                            newchild = ChildObject(m.ad_id, objectid, child_id, 'Computer')
                            self.db_session.add(newchild)

                if 'ChildOus' in arrays.keys():
                    if len(arrays['ChildOus']) > 0:
                        childobjects = arrays['ChildOus']['values']
                        for _, child_id in childobjects.items():
                            newchild = ChildObject(m.ad_id, objectid, child_id, 'OU')
                            self.db_session.add(newchild)

            self.db_session.commit()

        except Exception as ex:
            print('import_ou_v4', ex)

    def import_container_v4(self, bh_version, entries):
        """ Import BloodHound Container JSON data to database """
        try:
            objects = entries['objects']
            arrays = entries['arrays']
            values = entries['values']

            if 'ObjectIdentifier' not in values:
                return

            # isaclprotected = values['IsACLProtected']
            # isdeleted = values['IsDeleted']
            objectid = values['ObjectIdentifier']

            m = Container()

            if 'Properties' in objects.keys():
                values = objects['Properties']['values']

                if 'domainsid' in values:
                    m.ad_id = self.get_adid_by_sid(values['domainsid'])
                elif 'domain' in values:
                    m.ad_id = self.get_adid_by_name(values['domain'])

                if m.ad_id is None:
                    # TODO...unknown domain??? trusts maybe
                    return

                m.name = values['name'].split('@', 1)[0]
                m.objectGUID = objectid
                if values['distinguishedname']:
                    m.dn = values['distinguishedname']

            self.db_session.add(m)
            edgeinfo = EdgeLookup(m.ad_id, objectid, 'container')
            self.db_session.add(edgeinfo)
            self.db_session.commit()

            # add aces to global Ace table (these will be turned into edges later)
            if 'Aces' in arrays.keys():
                if len(arrays['Aces']) > 0:
                    self.add_aces(bh_version, m.ad_id, objectid, arrays['Aces']['objects'])

            if 'ChildObjects' in arrays.keys():
                if len(arrays['ChildObjects']) > 0:
                    childobjects = arrays['ChildObjects']['objects']
                    for _, child in childobjects.items():
                        values = child['values']
                        if bh_version == 4:
                            child_id = values['ObjectIdentifier']
                            child_type = values['ObjectType']
                            newchild = ChildObject(m.ad_id, objectid, child_id, child_type)
                            self.db_session.add(newchild)

            self.db_session.commit()
        except Exception as ex:
            print('import_container_v4', ex)

    def import_session(self):
        pass

    def insert_session_edges(self):
        """ Convert all rows in Session table into edges in Edge table """
        pass  # TODO

    def insert_spn_edges(self):
        """ Convert MSSQLSvc userSPNs to edges in Edge table """
        count = self.db_session.query(UserSPN).filter_by(service_class='MSSQLSvc').count()
        iterator = tqdm(range(0, count))

        q = self.db_session.query(UserSPN).filter_by(service_class='MSSQLSvc')
        for spn in windowed_query(q, UserSPN.id, 1000):
            s = ServiceSPN.from_userspn(spn)
            self.db_session.add(s)
            if spn.service_class == 'MSSQLSvc':
                res = self.db_session.query(Computer).filter_by(dNSHostName=spn.computername.upper()).filter(
                    Computer.ad_id == spn.ad_id).first()
                if res is not None:
                    dst = self.sid_to_id(res.objectSid, spn.ad_id)
                    src = self.sid_to_id(spn.owner_sid, spn.ad_id)
                    edge = Edge(spn.ad_id, src, dst, 'sqladmin')
                    self.db_session.add(edge)
                else:
                    pass
            iterator.update(1)
        self.db_session.query(UserSPN).delete()
        self.db_session.commit()

    def insert_members_edges(self):
        """ Convert all rows in Member table into edges in Edge table """
        count = self.db_session.query(Member).count()
        iterator = tqdm(range(0, count))

        q = self.db_session.query(Member)
        for member in windowed_query(q, Member.id, 1000):
            dst = self.sid_to_id(member.group_sid, member.ad_id)
            src = self.sid_to_id(member.member_sid, member.ad_id)
            edge = Edge(member.ad_id, src, dst, 'member')
            self.db_session.add(edge)
            iterator.update(1)
        self.db_session.query(Member).delete()
        self.db_session.commit()

    def insert_childobjects_edges(self):
        """ Convert all rows in ChildObject table into edges in Edge table """
        count = self.db_session.query(ChildObject).count()
        iterator = tqdm(range(0, count))

        q = self.db_session.query(ChildObject)
        for childobject in windowed_query(q, ChildObject.id, 1000):
            dst = self.sid_to_id(childobject.container_id, childobject.ad_id)
            src = self.sid_to_id(childobject.child_id, childobject.ad_id)
            edge = Edge(childobject.ad_id, src, dst, 'childobject')
            self.db_session.add(edge)
            iterator.update(1)
        self.db_session.query(ChildObject).delete()
        self.db_session.commit()

    def insert_gplink_edges(self):
        """ Convert all rows in Gplink table into edges in Edge table """
        count = self.db_session.query(Gplink).count()
        iterator = tqdm(range(0, count))

        q = self.db_session.query(Gplink)
        for link in windowed_query(q, Gplink.id, 1000):
            dst = self.sid_to_id(link.ou_guid, link.ad_id)
            src = self.sid_to_id(link.gpo_uid, link.ad_id)
            edge = Edge(link.ad_id, src, dst, 'gplink')
            self.db_session.add(edge)
            iterator.update(1)
        self.db_session.query(Gplink).delete()
        self.db_session.commit()

    def insert_ace_edges(self):
        """ Convert all rows in Ace table into edges in Edge table """
        count = self.db_session.query(Ace).count()
        iterator = tqdm(range(0, count))

        q = self.db_session.query(Ace)
        for ace in windowed_query(q, Ace.id, 1000):
            src = self.sid_to_id(ace.dst_sid, ace.ad_id)
            dst = self.sid_to_id(ace.src_sid, ace.ad_id)
            edge = Edge(ace.ad_id, src, dst, ace.label)
            self.db_session.add(edge)
            iterator.update(1)
        self.db_session.query(Ace).delete()
        self.db_session.commit()

    def from_zipfile(self, filepath):
        """ Given BloodHound zipped data file, unzip all to /tmp """
        with zipfile.ZipFile(filepath, 'r') as myzip:
            for names in myzip.namelist():
                try:
                    sys.stdout.write(f'Unzipping {names} to /tmp/{names}...')
                    myzip.extract(names, f'/tmp/')
                    sys.stdout.write(f'done\n')
                    self.json_files.append(f'/tmp/{names}')
                except Exception as ex:
                    print('Error', ex)

    def run(self):
        self.setup_db()

        # for all files in zip get meta information on them first
        all_json_files = {}
        for json_file in self.json_files:
            with open(json_file, 'rb') as f:
                data = f.read()
                data = data[-1000:]
                offset = data.find(b'"meta')
                test = data[offset:-1].strip(b'"meta":')
                meta = json.loads(test)
                all_json_files[meta['type']] = (meta, json_file)
                del data

        if 'domains' in all_json_files:
            print(f'\nImporting Domains')  # {all_json_files["domains"]}')
            with open(all_json_files['domains'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['domains'][0], f)

        if 'groups' in all_json_files:
            print(f'\nImporting Groups')  # {all_json_files["groups"]}')
            with open(all_json_files['groups'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['groups'][0], f)

        if 'users' in all_json_files:
            print(f'\nImporting Users')  # {all_json_files["users"]}')
            with open(all_json_files['users'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['users'][0], f)

        if 'computers' in all_json_files:
            print(f'\nImporting Computers')  # {all_json_files["computers"]}')
            with open(all_json_files['computers'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['computers'][0], f)

        if 'gpos' in all_json_files:
            print(f'\nImporting GPOs')  # {all_json_files["gpos"]}')
            with open(all_json_files['gpos'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['gpos'][0], f)

        if 'ous' in all_json_files:
            print(f'\nImporting OUs')  # {all_json_files["ous"]}')
            with open(all_json_files['ous'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['ous'][0], f)

        if 'containers' in all_json_files:
            print(f'\nImporting Containers')  # {all_json_files["containers"]}')
            with open(all_json_files['containers'][1], 'r') as f:
                self.json_parser.json_parser(all_json_files['containers'][0], f)

        # create edges
        # print('\nCreating edges from Sessions')
        # self.insert_session_edges()

        print('\nCreating edges from SPNs')
        self.insert_spn_edges()

        print('\nCreating edges from group memberships')
        self.insert_members_edges()

        print('\nCreating edges from childobjects')
        self.insert_childobjects_edges()

        print('\nCreating edges from gplinks')
        self.insert_gplink_edges()

        print('\nCreating edges from aces')
        self.insert_ace_edges()


class JsonParser:
    def __init__(self, bhimporter):
        self.bhimporter = bhimporter
        self.iterator = None  # holds tqdm progress tracker
        self.offset = 0  # data buffer offset
        self.data = ''  # raw json data
        self.datalen = 0
        self.bh_version = 0
        self.bh_type = ''  # bloodhound data type (computer, user, group...etc
        self.f = None

    def next_chunk(self):
        """ Get next chunk of file data """
        return read_file_chunk(self.f)

    def get_next_char(self):
        """ Get next character in data buffer (increments current offset) """
        self.offset = self.offset + 1
        if self.offset < self.datalen:
            return self.data[self.offset]
        else:
            self.data = self.next_chunk()
            self.datalen = len(self.data)
            self.offset = 0
            if self.offset < self.datalen:
                char = self.data[self.offset]
                return char
            else:
                return None

    def get_current_char(self):
        """ Get current character in data buffer (does not increment offset) """
        if self.offset < self.datalen:
            return self.data[self.offset]
        else:
            self.data = self.next_chunk()
            self.datalen = len(self.data)
            self.offset = 0
            if self.offset < self.datalen:
                return self.data[self.offset]
            else:
                return None

    def json_parser(self, meta, f):
        """ Parse JSON file containing BloodHound data """
        self.bh_version = meta['version']
        self.bh_type = meta['type']
        self.f = f
        self.data = self.next_chunk()  # get first chunk of JSON data
        self.datalen = len(self.data)
        self.offset = 0
        self.iterator = tqdm(total=meta['count'])

        # check for byte order mark (BOM)
        if self.data[0] != '{':
            bom = bytes(self.data[0], 'utf-8')
            if bom != b'\xef\xbb\xbf':
                print('FATAL! - not utf-8 encoding. Try another file')
                return
            self.offset = self.offset + 1

        char = self.get_current_char()
        while char is not None:
            if char and char == '{':
                _ = self.json_object_parser(json_type=JSON_TYPE_TOP_OBJECT)

            char = self.get_next_char()

        self.iterator.refresh()
        self.iterator.close()

    def json_object_parser(self, json_type=JSON_TYPE_ENTRY_VALUE):
        """ Handles the data between '{' and '}' during processing """
        entries = {}

        char = self.get_current_char()
        if char != '{':
            print('Error bad object', self.offset, self.data[self.offset])
            return
        else:
            char = self.get_next_char()
            while char is not None:
                if char == '}':
                    self.get_next_char()

                    if json_type == JSON_TYPE_ENTRY:
                        self.iterator.update(1)
                        self.bhimporter.json_handler(self.bh_type, self.bh_version, entries)
                        entries.clear()
                    break
                else:
                    entries = self.json_entries_parser(['}'], json_type)
                    char = self.get_current_char()

        return entries

    def json_array_parser(self, name='', json_type=JSON_TYPE_ENTRY_VALUE):
        """ Handles the data between '[' and ']' during processing """
        entries = {}

        char = self.get_current_char()
        if char != '[':
            print('Error bad array', self.data[self.offset])
            return
        else:
            char = self.get_next_char()
            while char is not None:
                if char == ']':
                    self.get_next_char()

                    # handle completely parsed array
                    if json_type == JSON_TYPE_TOP_NEXT:
                        if name != 'data':
                            pass
                    break
                else:
                    entries = self.json_entries_parser([']'], json_type)
                    char = self.get_current_char()

        return entries

    def json_entries_parser(self, end_chars, json_type=JSON_TYPE_ENTRY_VALUE):
        """ Generic parser of JSON entries (objects, arrays, and values) """
        entries = {'objects': {}, 'arrays': {}, 'values': {}}

        entry_name = ''
        idx = 0
        char = self.get_current_char()

        while char is not None:
            if char in end_chars:
                break
            elif char == '"':  # start of quoted string
                temp_str = self.read_json_string()
                char = self.get_current_char()
                if char == ':':
                    entry_name = temp_str
                    char = self.get_next_char()
                else:
                    if entry_name == '':
                        tmp_name = str(rando())
                    else:
                        tmp_name = entry_name
                    entries['values'][tmp_name] = temp_str
            elif char == '{':  # start of JSON object
                idx = idx + 1
                obj_entries = self.json_object_parser(json_type=json_type+1)
                if entry_name == '':
                    tmp_name = str(rando())
                else:
                    tmp_name = entry_name
                entries['objects'][tmp_name] = obj_entries
                char = self.get_current_char()
            elif char == '[':  # start of JSON array
                arr_entries = self.json_array_parser(name=entry_name, json_type=json_type+1)
                if entry_name == '':
                    tmp_name = str(rando())
                else:
                    tmp_name = entry_name
                entries['arrays'][tmp_name] = arr_entries
                char = self.get_current_char()
            elif char == ',':  # end of json entry
                char = self.get_next_char()
            else:  # new key/value entry
                entry_value = self.read_json_value(end_chars)
                if entry_name == '':
                    tmp_name = str(rando())
                else:
                    tmp_name = entry_name
                entries['values'][tmp_name] = entry_value
                char = self.get_current_char()

        return entries

    def read_json_value(self, end_chars):
        tmp_val = ''
        is_str = False
        ret_val = None

        char = self.get_current_char()
        while char is not None:
            if char == ',' or char in end_chars:
                break
            elif char == '"':
                is_str = True
                tmp_val = self.read_json_string()
                char = self.get_current_char()
            else:
                tmp_val = tmp_val + char
                char = self.get_next_char()

        if len(tmp_val) > 0 and is_str is False:
            try:
                if tmp_val == 'false':
                    ret_val = False
                elif tmp_val == 'true':
                    ret_val = True
                elif tmp_val == 'null':
                    ret_val = None
                else:
                    ret_val = int(tmp_val)
            except Exception as ex:
                ret_val = tmp_val
                print(f'Error: {ex}', self.offset, self.data[self.offset], tmp_val)
        elif len(tmp_val) > 0 and is_str is True:
            ret_val = tmp_val
        # else:
        #    print("WTF")
        #    input()

        return ret_val

    def read_json_string(self):
        ret_str = ''

        char = self.get_current_char()
        if char != '"':
            print('Bad string value', self.data[self.offset])
        else:
            char = self.get_next_char()
            while char is not None:
                if char == '\\':
                    char = self.get_next_char()
                    ret_str = ret_str + char
                    char = self.get_next_char()
                elif char == '"':
                    self.get_next_char()
                    break
                else:
                    ret_str = ret_str + char
                    char = self.get_next_char()

        return ret_str
