from sqlalchemy.sql.expression import func

from app import db
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
        self.nodes = []
        self.edges = []
        self.ncache = []
        self.ecache = []

    def name_to_sid(self, name):
        res = db.session.query(Group).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = db.session.query(ADUser).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = db.session.query(Machine).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = db.session.query(GPO).filter_by(name=name.upper()).first()
        if res:
            return res.objectGUID
        res = db.session.query(ADOU).filter_by(name=name.upper()).first()
        if res:
            return res.objectGUID
        return ''

    def autocomplete(self, text=b'', max_return=15):
        print('AUTOCOMPLETE called', text)
        text = text.decode('utf-8')
        matches = []

        res = db.session.query(Machine).filter(Machine.name.startswith(text.upper()))
        if res:
            for t in res:
                if len(matches) <= max_return:
                    matches.append(t.name)

        res = db.session.query(Group).filter(Group.name.startswith(text.upper()))
        if res:
            for t in res:
                if len(matches) <= max_return:
                    matches.append(t.name)

        res = db.session.query(ADUser).filter(ADUser.name.startswith(text.upper()))
        if res:
            for t in res:
                if len(matches) <= max_return:
                    matches.append(t.name)

        res = db.session.query(GPO).filter(GPO.name.startswith(text.upper()))
        if res:
            for t in res:
                if len(matches) <= max_return:
                    matches.append(t.name)

        res = db.session.query(ADOU).filter(ADOU.name.startswith(text.upper()))
        if res:
            for t in res:
                if len(matches) <= max_return:
                    matches.append(t.name)

        print('returning matches', matches)
        return json.dumps(matches)

    def graph_update(self, json_data):
        final = {'nodes': {}, 'edges': {}}

        max_depth = 99
        if 'max_depth' in json_data:
            max_depth = json_data['max_depth']
            print('testing', type(max_depth), max_depth)

        edge_list = []
        if 'edges' in json_data:
            edge_list = json_data['edges']

        # reset network variables
        self.nodes = []
        self.edges = []
        self.ncache = []
        self.ecache = []

        # take action based on submit_type
        if json_data['submit_type'] == 'shortest_path_dst':
            # oid = 'S-1-5-21-3937601378-3721788405-2067139823-512'
            oid = self.name_to_sid(json_data['dst'])
            self.path_to_dst(oid, max_depth=max_depth, edge_list=edge_list)
        elif json_data['submit_type'] == 'shortest_path_src_dst':
            src = self.name_to_sid(json_data['src'])
            dst = self.name_to_sid(json_data['dst'])
            self.path_src_to_dst(src, dst, max_depth=max_depth, edge_list=edge_list)
        elif json_data['submit_type'] == 'kerberoastable_users':
            self.kerberoastable_users()
        else:
            return final

        idx = 0
        for node in self.nodes:
            final['nodes'][str(idx)] = node
            idx = idx + 1

        idx = 0
        for edge in self.edges:
            final['edges'][str(idx)] = edge
            idx = idx + 1

        return json.dumps(final)

    def kerberoastable_users(self):
        res = db.session.query(ADUser).filter(func.length(ADUser.servicePrincipalName) > 0)
        if res:
            for user in res:
                self.nodes.append(make_node(user.objectSid, user.name, 'user', 0))

    def path_to_dst(self, oid, max_depth=5, edge_list=None):
        self.add_node_recursive([oid], max_depth=max_depth, edge_list=edge_list)

    def path_src_to_dst(self, src, dst, max_depth=99, edge_list=None):
        self.add_node_recursive([dst], max_depth=max_depth, edge_list=edge_list)

        graph = {}
        for edge in self.edges:
            a, b = edge['to'], edge['from']

            if a not in graph.keys():
                graph[a] = []
            if b not in graph.keys():
                graph[b] = []

            graph[a].append(b)
            graph[b].append(a)
        # print('TESTING', graph)

        explored = []

        # Queue for traversing the graph in the BFS
        queue = [[src]]

        # If the desired node is reached
        if src == dst:
            print("SRC and DST are equal")
            tmp_nodes = []
            for node in self.nodes:
                if node['id'] in dst:
                    tmp_nodes.append(node)
            self.nodes = tmp_nodes
            self.edges = []
            return

        if src not in graph.keys():
            print('No path from src to dst could be found')
            self.nodes = []
            self.edges = []
            return

        # Loop to traverse the graph with the help of the queue
        while queue:
            path = queue.pop(0)
            node = path[-1]

            # Condition to check if the current node is not visited
            if node not in explored:
                neighbours = graph[node]

                # Loop to iterate over the neighbours of the node
                for neighbour in neighbours:
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)

                    # Condition to check if the neighbour node is the goal
                    if neighbour == dst:
                        print("Shortest path = ", *new_path)

                        tmp_nodes = []
                        for node in self.nodes:
                            if node['id'] in new_path:
                                tmp_nodes.append(node)
                        self.nodes = tmp_nodes

                        tmp_edges = []
                        for edge in self.edges:
                            if edge['to'] in new_path and edge['from'] in new_path:
                                tmp_edges.append(edge)
                        self.edges = tmp_edges

                        return
                explored.append(node)

        # Condition when the nodes are not connected
        print('No path from src to dst could be found')
        self.nodes = []
        self.edges = []
        return

    def add_node_recursive(self, sids, depth=0, max_depth=5, edge_list=None):
        id_sid_map = {}

        if depth > max_depth:
            return

        for sid in sids:
            start = db.session.query(EdgeLookup).filter_by(oid=sid).first()  # get id and typefrom sid
            if start:
                if start.oid not in self.ncache:
                    self.ncache.append(start.oid)
                    if start.otype == 'group':
                        new_node = db.session.query(Group).filter_by(objectSid=start.oid).first()
                        self.nodes.append(make_node(new_node.objectSid, new_node.name, 'group', depth))
                    elif start.otype == 'user':
                        new_node = db.session.query(ADUser).filter_by(objectSid=start.oid).first()
                        self.nodes.append(make_node(new_node.objectSid, new_node.name, 'user', depth))
                    elif start.otype == 'machine':
                        new_node = db.session.query(Machine).filter_by(objectSid=start.oid).first()
                        self.nodes.append(make_node(new_node.objectSid, new_node.name, 'computer', depth))
                    elif start.otype == 'gpo':
                        new_node = db.session.query(GPO).filter_by(objectGUID=start.oid).first()
                        self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'gpo', depth))
                    elif start.otype == 'ou':
                        new_node = db.session.query(ADOU).filter_by(objectGUID=start.oid).first()
                        self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'ou', depth))
                    else:
                        print('UNKNOWN!@!!!!!!!', start.otype)
                    id_sid_map[start.id] = start.oid

        for node_id, node_sid in id_sid_map.items():
            self.get_edges(node_id, node_sid, depth, edge_list=edge_list)

    def get_edges(self, edgeid, sid, depth=0, edge_list=None):
        edges_query = db.session.query(Edge).filter_by(dst=edgeid)  # get edges from id

        new_nodes = []

        idx = 0
        for e in edges_query:  # for all edges
            if edge_list and e.label in edge_list:
                res = db.session.query(EdgeLookup).filter_by(id=e.src).first()  # get oid and otype from edge src

                if (res.oid, sid, e.label) not in self.ecache and res.oid != sid and res.oid not in self.ncache:
                    self.ecache.append((res.oid, sid, e.label))
                    self.edges.append(make_edge(str(idx), res.oid, sid, e.label))
                    idx = idx + 1

                    if res.oid not in self.ncache:
                        new_nodes.append(res.oid)

        if len(new_nodes) > 0:
            self.add_node_recursive(new_nodes, depth+1, edge_list=edge_list)

    def get_extended_info(self, oid):
        ret = ''
        oid = oid.decode('utf-8')

        res = db.session.query(EdgeLookup).filter_by(oid=oid).first()  # get id and typefrom sid
        if res:
            if res.otype == 'group':
                obj = db.session.query(Group).filter_by(objectSid=res.oid).first()
                ret = self.group_display(obj)
            elif res.otype == 'user':
                obj = db.session.query(ADUser).filter_by(objectSid=res.oid).first()
                ret = self.user_display(obj)
            elif res.otype == 'machine':
                obj = db.session.query(Machine).filter_by(objectSid=res.oid).first()
                ret = self.computer_display(obj)
            elif res.otype == 'gpo':
                obj = db.session.query(GPO).filter_by(objectGUID=res.oid).first()
            elif res.otype == 'ou':
                obj = db.session.query(ADOU).filter_by(objectGUID=res.oid).first()
            else:
                print('UNKNOWN!@!!!!!!!')
        return ret

    def group_display(self, obj):
        ret = group_table
        ret = ret.replace('{{Name}}', obj.name)
        ret = ret.replace('{{Sid}}', obj.objectSid)
        ret = ret.replace('{{Description}}', obj.description)
        return ret

    def user_display(self, obj):
        ret = group_table
        ret = ret.replace('{{Name}}', obj.name)
        ret = ret.replace('{{Sid}}', obj.objectSid)
        ret = ret.replace('{{Description}}', obj.description)
        return ret

    def computer_display(self, obj):
        ret = group_table
        ret = ret.replace('{{Name}}', obj.name)
        ret = ret.replace('{{Sid}}', obj.objectSid)
        ret = ret.replace('{{Description}}', obj.description)
        return ret
