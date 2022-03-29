from app import bloodrooster_app
from dbmodel import *

group_table = ''' <table class="table">
  <thead>
    <tr>
      <th scope="col"></th>
      <th scope="col"></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Name</th>
      <td>{{Name}}</td>
    </tr>
    <tr>
      <th scope="row">SID</th>
      <td>{{Sid}}</td>
    </tr>
    <tr>
      <th scope="row">Description</th>
      <td>{{Description}}</td>
    </tr>
  </tbody>
</table> '''


def make_node(node_id, node_name, node_type, depth=0):
    # print('Adding node', node_id, node_name)
    return {'id': node_id, 'name': node_name, 'type': node_type, 'group': depth}


def make_edge(edge_id, edge_from, edge_to, edge_label):
    # print('Adding edge', edge_from, edge_to, edge_label)
    return {'id': edge_id, 'from': edge_from, 'to': edge_to, 'label': edge_label}


class BloodRoostrWebApp:
    def __init__(self):
        self.db_conn = bloodrooster_app.config['SQLALCHEMY_DATABASE_URI']
        self.db_session = get_session(self.db_conn)

    def name_to_sid(self, name):
        res = self.db_session.query(Group).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = self.db_session.query(ADUser).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = self.db_session.query(Machine).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = self.db_session.query(GPO).filter_by(name=name.upper()).first()
        if res:
            return res.objectGUID
        res = self.db_session.query(ADOU).filter_by(name=name.upper()).first()
        if res:
            return res.objectGUID
        return ''

    def graph_update(self, json_data):
        final = {'nodes': {}, 'edges': {}}
        max_depth = 99

        if 'max_depth' in json_data:
            max_depth = json_data['max_depth']
            print('testing', type(max_depth), max_depth)

        oid = ''
        if json_data['submit_type'] == 'shortest_path_dst':
            oid = self.name_to_sid(json_data['dst'])
        # elif json_data['submit_type'] ==
        else:
            return final

        nodes = []
        edges = []
        ncache = []
        ecache = []

        # oid = 'S-1-5-21-3937601378-3721788405-2067139823-512'
        # nodes, edges, ncache, ecache = self.pathto(testsid, nodes, edges, ncache, ecache)
        nodes, edges, ncache, ecache = self.add_node([oid], nodes, edges, ncache, ecache)

        idx = 0
        for node in nodes:
            final['nodes'][str(idx)] = node
            idx = idx + 1

        idx = 0
        for edge in edges:
            final['edges'][str(idx)] = edge
            idx = idx + 1

        return json.dumps(final)

    def add_node(self, sids, nodes, edges, ncache, ecache, depth=0, max_depth=5):
        id_sid_map = {}

        if depth > max_depth:
            return nodes, edges, ncache, ecache

        for sid in sids:
            start = self.db_session.query(EdgeLookup).filter_by(oid=sid).first()  # get id and typefrom sid
            if start:
                if start.oid not in ncache:
                    ncache.append(start.oid)
                    if start.otype == 'group':
                        new_node = self.db_session.query(Group).filter_by(objectSid=start.oid).first()
                        nodes.append(make_node(new_node.objectSid, new_node.name, 'group', depth))
                    elif start.otype == 'user':
                        new_node = self.db_session.query(ADUser).filter_by(objectSid=start.oid).first()
                        nodes.append(make_node(new_node.objectSid, new_node.name, 'user', depth))
                    elif start.otype == 'machine':
                        new_node = self.db_session.query(Machine).filter_by(objectSid=start.oid).first()
                        nodes.append(make_node(new_node.objectSid, new_node.name, 'computer', depth))
                    elif start.otype == 'gpo':
                        new_node = self.db_session.query(GPO).filter_by(objectGUID=start.oid).first()
                        nodes.append(make_node(new_node.objectGUID, new_node.name, 'gpo', depth))
                    elif start.otype == 'ou':
                        new_node = self.db_session.query(ADOU).filter_by(objectGUID=start.oid).first()
                        nodes.append(make_node(new_node.objectGUID, new_node.name, 'ou', depth))
                    else:
                        print('UNKNOWN!@!!!!!!!')
                    id_sid_map[start.id] = start.oid

        for node_id, node_sid in id_sid_map.items():
            nodes, edges, ncache, ecache = self.get_edges(node_id, node_sid, nodes, edges, ncache, ecache, depth)
        return nodes, edges, ncache, ecache

    def get_edges(self, edgeid, sid, nodes, edges, ncache, ecache, depth=0):
        edges_query = self.db_session.query(Edge).filter_by(dst=edgeid)  # get edges from id

        new_nodes = []

        idx = 0
        for e in edges_query:  # for all edges
            res = self.db_session.query(EdgeLookup).filter_by(id=e.src).first()  # get oid and otype from edge src

            if (res.oid, sid, e.label) not in ecache and res.oid != sid and res.oid not in ncache:
                ecache.append((res.oid, sid, e.label))
                edges.append(make_edge(str(idx), res.oid, sid, e.label))
                idx = idx + 1

                if res.oid not in ncache:
                    new_nodes.append(res.oid)

        if len(new_nodes) > 0:
            nodes, edges, ncache, ecache = self.add_node(new_nodes, nodes, edges, ncache, ecache, depth+1)

        return nodes, edges, ncache, ecache

    def get_extended_info(self, oid):
        ret = ''
        print('HERE!!!!', oid)
        oid = oid.decode('utf-8')
        print('AND HERE!!!!', oid)

        res = self.db_session.query(EdgeLookup).filter_by(oid=oid).first()  # get id and typefrom sid
        if res:
            if res.otype == 'group':
                obj = self.db_session.query(Group).filter_by(objectSid=res.oid).first()
                ret = self.group_display(obj)
            elif res.otype == 'user':
                obj = self.db_session.query(ADUser).filter_by(objectSid=res.oid).first()
                ret = self.user_display(obj)
            elif res.otype == 'machine':
                obj = self.db_session.query(Machine).filter_by(objectSid=res.oid).first()
                ret = self.computer_display(obj)
            elif res.otype == 'gpo':
                obj = self.db_session.query(GPO).filter_by(objectGUID=res.oid).first()
            elif res.otype == 'ou':
                obj = self.db_session.query(ADOU).filter_by(objectGUID=res.oid).first()
            else:
                print('UNKNOWN!@!!!!!!!')
        return ret

    def group_display(self, obj):
        ret = group_table
        ret = ret.replace('{{Name}}', obj.name)
        ret = ret.replace('{{Sid}}', obj.objectSid)
        ret = ret.replace('{{Description}}', obj.description)
        print('TESTING!!!!', ret)
        return ret

    def user_display(self, obj):
        ret = group_table
        ret = ret.replace('{{Name}}', obj.name)
        ret = ret.replace('{{Sid}}', obj.objectSid)
        ret = ret.replace('{{Description}}', obj.description)
        print('TESTING!!!!', ret)
        return ret

    def computer_display(self, obj):
        ret = group_table
        ret = ret.replace('{{Name}}', obj.name)
        ret = ret.replace('{{Sid}}', obj.objectSid)
        ret = ret.replace('{{Description}}', obj.description)
        print('TESTING!!!!', ret)
        return ret
