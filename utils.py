from dbmodel import Group, User, Computer, Ou, GPO


extended_info_template_start = '''
<table class="table">
  <thead>
    <tr>
      <th scope="col"></th>
      <th scope="col"></th>
    </tr>
  </thead>
  <tbody>
'''

extended_info_template_end = '''
  </tbody>
</table>
'''

extended_info_template_item = '''
    <tr>
      <th scope="row">{{Name}}</th>
      <td>{{Value}}</td>
    </tr>
'''


def create_extended_info_item(name, value):
    ret = extended_info_template_item
    ret = ret.replace('{{Name}}', name)
    ret = ret.replace('{{Value}}', value)
    return ret


def make_node(node_id, node_name, node_type, depth=0):
    # print('Adding node', node_id, node_name)
    return {'id': node_id, 'name': node_name, 'type': node_type, 'group': depth}


def make_edge(edge_id, edge_from, edge_to, edge_label):
    # print('Adding edge', edge_from, edge_to, edge_label)
    return {'id': edge_id, 'from': edge_from, 'to': edge_to, 'label': edge_label}


def group_display(obj):
    if not isinstance(obj, Group):
        return ''

    ret = extended_info_template_start
    if obj.name and len(obj.name) > 0:
        ret = ret + create_extended_info_item('Name', obj.name)
    if obj.objectSid and len(obj.objectSid) > 0:
        ret = ret + create_extended_info_item('SID', obj.objectSid)
    if obj.description and len(obj.description) > 0:
        ret = ret + create_extended_info_item('Description', obj.description)
    if obj.dn and len(obj.dn) > 0:
        ret = ret + create_extended_info_item('Distinguished Name', obj.dn)
    return ret + extended_info_template_end


def user_display(obj):
    if not isinstance(obj, User):
        return ''

    ret = extended_info_template_start
    if obj.name and len(obj.name) > 0:
        ret = ret + create_extended_info_item('Name', obj.name)
    if obj.objectSid and len(obj.objectSid) > 0:
        ret = ret + create_extended_info_item('SID', obj.objectSid)
    if obj.description and len(obj.description) > 0:
        ret = ret + create_extended_info_item('Description', obj.description)
    if obj.dn and len(obj.dn) > 0:
        ret = ret + create_extended_info_item('Distinguished Name', obj.dn)
    if obj.servicePrincipalName and len(obj.servicePrincipalName) > 0:
        ret = ret + create_extended_info_item('Service Principal Name', obj.servicePrincipalName)
    if obj.lastLogon:
        ret = ret + create_extended_info_item('Last Logon', str(obj.lastLogon))
    if obj.pwdLastSet:
        ret = ret + create_extended_info_item('Password Last Set', str(obj.pwdLastSet))
    return ret + extended_info_template_end


def computer_display(obj):
    if not isinstance(obj, Computer):
        return ''

    ret = extended_info_template_start
    if obj.name and len(obj.name) > 0:
        ret = ret + create_extended_info_item('Name', obj.name)
    if obj.objectSid and len(obj.objectSid) > 0:
        ret = ret + create_extended_info_item('SID', obj.objectSid)
    if obj.description and len(obj.description) > 0:
        ret = ret + create_extended_info_item('Description', obj.description)
    if obj.dn and len(obj.dn) > 0:
        ret = ret + create_extended_info_item('Distinguished Name', obj.dn)
    if obj.operatingSystem and len(obj.operatingSystem) > 0:
        ret = ret + create_extended_info_item('Operating System', obj.operatingSystem)
    if obj.lastLogonTimestamp:
        ret = ret + create_extended_info_item('Last Logon Timestamp', str(obj.lastLogonTimestamp))
    if obj.pwdLastSet:
        ret = ret + create_extended_info_item('Password Last Set', str(obj.pwdLastSet))
    if obj.servicePrincipalName and len(obj.servicePrincipalName) > 0:
        ret = ret + create_extended_info_item('Service Principal Name(s)', obj.servicePrincipalName)
    return ret + extended_info_template_end


def ou_display(obj):
    if not isinstance(obj, Ou):
        return ''

    ret = extended_info_template_start
    if obj.name and len(obj.name) > 0:
        ret = ret + create_extended_info_item('Name', obj.name)
    if obj.objectSid and len(obj.objectSid) > 0:
        ret = ret + create_extended_info_item('GUID', obj.objectGUID)
    if obj.description and len(obj.description) > 0:
        ret = ret + create_extended_info_item('Description', obj.description)
    if obj.dn and len(obj.dn) > 0:
        ret = ret + create_extended_info_item('Distinguished Name', obj.dn)
    return ret + extended_info_template_end


def gpo_display(obj):
    if not isinstance(obj, GPO):
        return ''

    ret = extended_info_template_start
    if obj.name and len(obj.name) > 0:
        ret = ret + create_extended_info_item('Name', obj.name)
    if obj.objectSid and len(obj.objectSid) > 0:
        ret = ret + create_extended_info_item('GUID', obj.objectGUID)
    if obj.description and len(obj.description) > 0:
        ret = ret + create_extended_info_item('Description', obj.description)
    if obj.dn and len(obj.dn) > 0:
        ret = ret + create_extended_info_item('Distinguished Name', obj.dn)
    if obj.path and len(obj.path) > 0:
        ret = ret + create_extended_info_item('Path', obj.path)
    return ret + extended_info_template_end
