from sqlalchemy.sql.expression import func

from app import db
from dbmodel import *
from .utils import make_node, make_edge, group_display, user_display, computer_display, ou_display, gpo_display
from .utils import user_list_display, domain_display, computer_list_display


class BloodRoosterWebApp:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.ncache = []
        self.ecache = []

    def name_to_sid(self, name):
        res = db.session.query(Group).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = db.session.query(User).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = db.session.query(Computer).filter_by(name=name.upper()).first()
        if res:
            return res.objectSid
        res = db.session.query(GPO).filter_by(name=name.upper()).first()
        if res:
            return res.objectGUID
        res = db.session.query(Ou).filter_by(name=name.upper()).first()
        if res:
            return res.objectGUID
        return ''

    def autocomplete(self, json_data, max_return=15):
        autocomplete_type = json_data['type']
        text = json_data['text']
        matches = []

        limit = max_return

        if autocomplete_type == 'all':
            res = db.session.query(Computer).filter(Computer.name.startswith(text.upper())).limit(limit)
            if res:
                for t in res:
                    if len(matches) <= max_return:
                        matches.append(t.name)
                limit = limit - len(matches)

            if limit > 0:
                res = db.session.query(Group).filter(Group.name.startswith(text.upper())).limit(limit)
                if res:
                    for t in res:
                        if len(matches) <= max_return:
                            matches.append(t.name)
                    limit = limit - len(matches)

            if limit > 0:
                res = db.session.query(User).filter(User.name.startswith(text.upper())).limit(limit)
                if res:
                    for t in res:
                        if len(matches) <= max_return:
                            matches.append(t.name)
                    limit = limit - len(matches)

            if limit > 0:
                res = db.session.query(GPO).filter(GPO.name.startswith(text.upper())).limit(limit)
                if res:
                    for t in res:
                        if len(matches) <= max_return:
                            matches.append(t.name)
                    limit = limit - len(matches)

            if limit > 0:
                res = db.session.query(Ou).filter(Ou.name.startswith(text.upper())).limit(limit)
                if res:
                    for t in res:
                        if len(matches) <= max_return:
                            matches.append(t.name)
                    limit = limit - len(matches)

            if limit > 0:
                res = db.session.query(Container).filter(Container.name.startswith(text.upper())).limit(limit)
                if res:
                    for t in res:
                        if len(matches) <= max_return:
                            matches.append(t.name)
                    # limit = limit - len(matches)

        elif autocomplete_type == 'domain':
            res = db.session.query(Domain).filter(Domain.name.startswith(text.upper())).limit(limit)
            if res:
                for t in res:
                    if len(matches) <= max_return:
                        matches.append(t.name)

        elif autocomplete_type == 'group':
            res = db.session.query(Group).filter(Group.name.startswith(text.upper())).limit(limit)
            if res:
                for t in res:
                    if len(matches) <= max_return:
                        matches.append(t.name)

        print('returning matches', matches)
        return json.dumps(matches)

    def graph_update(self, json_data):
        final = {'nodes': {}, 'edges': {}}

        max_depth = 10
        if 'max_depth' in json_data and json_data['max_depth'] is not None and len(json_data['max_depth']) > 0:
            max_depth = int(json_data['max_depth'])
            print('testing', type(max_depth), max_depth)

        max_nodes = 100
        if 'max_nodes' in json_data and json_data['max_nodes'] is not None and len(json_data['max_nodes']) > 0:
            max_nodes = int(json_data['max_nodes'])
            print('testing', type(max_nodes), max_nodes)

        edge_list = []
        if 'edges' in json_data:
            edge_list = json_data['edges']

        # reset network variables
        self.nodes = []
        self.edges = []
        self.ncache = []
        self.ecache = []

        print('GRAPHA updatre!!!!', json_data)

        # take action based on submit_type
        if json_data['submit_type'] == 'shortest_path_dst':
            oid = self.name_to_sid(json_data['dst'])
            self.path_to_dst(oid, max_depth=max_depth, edge_list=edge_list)
        elif json_data['submit_type'] == 'shortest_path_src':
            oid = self.name_to_sid(json_data['src'])
            self.path_to_dst(oid, max_depth=max_depth, edge_list=edge_list)
        elif json_data['submit_type'] == 'shortest_path_src_dst':
            src = self.name_to_sid(json_data['src'])
            dst = self.name_to_sid(json_data['dst'])
            self.path_src_to_dst(src, dst, max_depth=max_depth, edge_list=edge_list)
        elif json_data['submit_type'] == 'kerberoastable_users':
            self.kerberoastable_users()
        elif json_data['submit_type'] == 'asreproastable_users':
            self.asreproastable_users()
        elif json_data['submit_type'] == 'dcsync_objects':
            self.dcsync_objects()
        elif json_data['submit_type'] == 'lapsusers':
            self.laps_users(max_nodes)
        elif json_data['submit_type'] == 'unconstrained_delegation':
            self.unconstrained_delegation()
        elif json_data['submit_type'] == 'surrounding_nodes':
            src = self.name_to_sid(json_data['src'])
            self.surrounding_nodes(src, max_depth=1, max_nodes=max_nodes, edge_list=edge_list)
        elif json_data['submit_type'] == 'expand':
            self.surrounding_nodes(json_data['src'], max_depth=1, max_nodes=max_nodes, edge_list=edge_list)
        elif json_data['submit_type'] == 'get_members':
            group_sid = self.name_to_sid(json_data['group'])
            self.get_members(group_sid)
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

    def get_members(self, sid):
        self.add_node2(sid, 'group')
        res = db.session.query(EdgeLookup).filter_by(oid=sid).first()
        if res:
            member_edges = db.session.query(Edge).filter_by(dst=res.id, label='member')
            if member_edges:
                idx = 0
                for member_edge in member_edges:
                    res2 = db.session.query(EdgeLookup).filter_by(id=member_edge.src).first()
                    if res2:
                        self.add_node2(res2.oid, res2.otype)
                        self.edges.append(make_edge(idx, sid, res2.oid, 'member'))
                    idx = idx + 1

    def kerberoastable_users(self):
        res = db.session.query(User).filter(func.length(User.servicePrincipalName) > 0)
        if res:
            self.nodes.append(make_node('kerberoastable', 'Kerberoastable', 'user_list', 0))

    def asreproastable_users(self):
        res = db.session.query(User).filter(User.UAC_DONT_REQUIRE_PREAUTH)
        if res:
            self.nodes.append(make_node('asreproastable', 'AS-REP Roastable', 'user_list', 0))

    def dcsync_objects(self):
        res = db.session.query(Domain).first()
        if res:
            self.nodes.append(make_node(res.objectSid, res.name, 'domain', 0))
            start = db.session.query(EdgeLookup).filter_by(oid=res.objectSid).first()
            if start:
                edges_query = db.session.query(Edge).filter_by(dst=start.id)
                if edges_query:
                    idx = 0
                    for edge in edges_query:
                        if edge.label == 'GetChanges' or edge.label == 'GetChangesAll':
                            res2 = db.session.query(EdgeLookup).filter_by(id=edge.src).first()
                            if res2:
                                self.edges.append(make_edge(str(idx), res2.oid, res.objectSid, edge.label))
                                idx = idx + 1
                                self.add_node(res2.oid, res.objectSid, edge.label, 1, True)

    def laps_users(self, max_nodes=100):
        edges = db.session.query(Edge).filter_by(label='ReadLAPSPassword')
        if edges:
            self.nodes.append(make_node('lapsusers', 'LAPS Users', 'user_list', 0))
            idx = 0
            for edge in edges:
                src = db.session.query(EdgeLookup).filter_by(id=edge.src).first()
                if src:
                    self.add_node2(src.oid, src.otype)

                dst = db.session.query(EdgeLookup).filter_by(id=edge.dst).first()
                if dst:
                    self.add_node2(dst.oid, dst.otype)
                self.edges.append(make_edge(idx, src, dst, 'ReadLAPSPassword'))
                idx = idx + 1

                if len(self.nodes) > max_nodes:
                    break

    def unconstrained_delegation(self):
        res = db.session.query(Computer).filter(Computer.UAC_TRUSTED_FOR_DELEGATION)
        if res:
            self.nodes.append(make_node('unconstrained_delegation', 'Unconstrained Delegation', 'computer_list', 0))

    def surrounding_nodes(self, src, max_depth=1, max_nodes=100, edge_list=None):
        print('SUROUNDING NOEDS', src)
        self.add_node_recursive([src], 'forward', max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)

    def path_to_dst(self, oid, max_depth=5, max_nodes=100, edge_list=None):
        self.add_node_recursive([oid], max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)

    def path_src_to_dst(self, src, dst, max_depth=10, max_nodes=100, edge_list=None):
        self.add_node_recursive([dst], max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)

        graph = {}
        for edge in self.edges:
            a, b = edge['to'], edge['from']

            if a not in graph.keys():
                graph[a] = []
            if b not in graph.keys():
                graph[b] = []

            graph[a].append(b)
            graph[b].append(a)

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

    def add_node2(self, oid, otype):
        if otype == 'group':
            new_node = db.session.query(Group).filter_by(objectSid=oid).first()
            self.nodes.append(make_node(new_node.objectSid, new_node.name, 'group', 0))
        elif otype == 'user':
            new_node = db.session.query(User).filter_by(objectSid=oid).first()
            self.nodes.append(make_node(new_node.objectSid, new_node.name, 'user', 0))
        elif otype == 'machine':
            new_node = db.session.query(Computer).filter_by(objectSid=oid).first()
            self.nodes.append(make_node(new_node.objectSid, new_node.name, 'computer', 0))
        elif otype == 'gpo':
            new_node = db.session.query(GPO).filter_by(objectGUID=oid).first()
            self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'gpo', 0))
        elif otype == 'ou':
            new_node = db.session.query(Ou).filter_by(objectGUID=oid).first()
            self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'ou', 0))
        elif otype == 'container':
            new_node = db.session.query(Container).filter_by(objectGUID=oid).first()
            self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'container', 0))
        else:
            print('UNKNOWN!@!!!!!!!', otype)

    def add_node(self, sid, parent_oid, edge_label, depth=0, expand_group=False):
        id_sid_map = {}

        start = db.session.query(EdgeLookup).filter_by(oid=sid).first()  # get id and typefrom sid
        if start:
            if start.oid not in self.ncache:
                self.ncache.append(start.oid)
                if start.otype == 'group':
                    if expand_group is True:
                        self.get_group_member_nodes(start, parent_oid, edge_label)
                    else:
                        new_node = db.session.query(Group).filter_by(objectSid=start.oid).first()
                        self.nodes.append(make_node(new_node.objectSid, new_node.name, 'group', depth))
                elif start.otype == 'user':
                    new_node = db.session.query(User).filter_by(objectSid=start.oid).first()
                    self.nodes.append(make_node(new_node.objectSid, new_node.name, 'user', depth))
                elif start.otype == 'machine':
                    new_node = db.session.query(Computer).filter_by(objectSid=start.oid).first()
                    self.nodes.append(make_node(new_node.objectSid, new_node.name, 'computer', depth))
                elif start.otype == 'gpo':
                    new_node = db.session.query(GPO).filter_by(objectGUID=start.oid).first()
                    self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'gpo', depth))
                elif start.otype == 'ou':
                    new_node = db.session.query(Ou).filter_by(objectGUID=start.oid).first()
                    self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'ou', depth))
                elif start.otype == 'container':
                    new_node = db.session.query(Container).filter_by(objectGUID=start.oid).first()
                    self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'container', depth))
                else:
                    print('UNKNOWN!@!!!!!!!', start.otype)
                id_sid_map[start.id] = start.oid

    def get_group_member_nodes(self, group_obj, parent_oid, edge_label):
        edges_query = db.session.query(Edge).filter_by(dst=group_obj.id)
        if edges_query:
            for edge in edges_query:
                if edge.label == 'member':
                    res2 = db.session.query(EdgeLookup).filter_by(id=edge.src).first()
                    if res2:
                        self.add_node(res2.oid, parent_oid, edge_label, 1, True)
                        self.edges.append(make_edge(res2.oid, res2.oid, parent_oid, edge_label))

    def add_node_recursive(self, sids, direction='back', depth=0, max_depth=5, max_nodes=100, edge_list=None):
        id_sid_map = {}

        if depth > max_depth or len(self.nodes) > max_nodes:
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
                        new_node = db.session.query(User).filter_by(objectSid=start.oid).first()
                        self.nodes.append(make_node(new_node.objectSid, new_node.name, 'user', depth))
                    elif start.otype == 'machine':
                        new_node = db.session.query(Computer).filter_by(objectSid=start.oid).first()
                        self.nodes.append(make_node(new_node.objectSid, new_node.name, 'computer', depth))
                    elif start.otype == 'gpo':
                        new_node = db.session.query(GPO).filter_by(objectGUID=start.oid).first()
                        self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'gpo', depth))
                    elif start.otype == 'ou':
                        new_node = db.session.query(Ou).filter_by(objectGUID=start.oid).first()
                        self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'ou', depth))
                    elif start.otype == 'container':
                        new_node = db.session.query(Container).filter_by(objectGUID=start.oid).first()
                        self.nodes.append(make_node(new_node.objectGUID, new_node.name, 'container', depth))
                    else:
                        print('UNKNOWN!@!!!!!!!', start.otype)
                    id_sid_map[start.id] = start.oid

        if depth > max_depth or len(self.nodes) > max_nodes:
            return

        for node_id, node_sid in id_sid_map.items():
            if direction == 'back':
                self.get_edges_back(node_id, node_sid, depth, max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)
            elif direction == 'forward':
                self.get_edges_forward(node_id, node_sid, depth, max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)

    def get_edges_back(self, edgeid, sid, depth=0, max_depth=5, max_nodes=100, edge_list=None):
        if len(self.nodes) < max_nodes:
            edges_query = db.session.query(Edge).filter_by(dst=edgeid).limit(max_nodes-len(self.nodes)).all()

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
                self.add_node_recursive(new_nodes, 'back', depth+1, max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)

    def get_edges_forward(self, edgeid, sid, depth=0, max_depth=5, max_nodes=100, edge_list=None):
        if len(self.nodes) < max_nodes:
            edges_query = db.session.query(Edge).filter_by(src=edgeid).limit(max_nodes-len(self.nodes)).all()

            new_nodes = []

            idx = 0
            for e in edges_query:  # for all edges
                if edge_list and e.label in edge_list:
                    res = db.session.query(EdgeLookup).filter_by(id=e.dst).first()  # get oid and otype from edge dst

                    if (sid, res.oid, e.label) not in self.ecache and res.oid != sid and res.oid not in self.ncache:
                        self.ecache.append((sid, res.oid, e.label))
                        self.edges.append(make_edge(str(idx), sid, res.oid, e.label))
                        idx = idx + 1

                        if res.oid not in self.ncache:
                            new_nodes.append(res.oid)
                else:
                    print('just some testing', e.label)

            if len(new_nodes) > 0:
                self.add_node_recursive(new_nodes, 'forward', depth+1, max_depth=max_depth, max_nodes=max_nodes, edge_list=edge_list)

    def get_extended_info(self, nodeid):
        ret = ''
        nodeid = nodeid.decode('utf-8')

        if nodeid == 'kerberoastable':
            res = db.session.query(User).filter(func.length(User.servicePrincipalName) > 0)
            if res:
                ret = user_list_display(res)
        elif nodeid == 'asreproastable':
            res = db.session.query(User).filter(User.UAC_DONT_REQUIRE_PREAUTH)
            if res:
                ret = user_list_display(res)
        elif nodeid == 'lapsusers':
            pass
        elif nodeid == 'unconstrained_delegation':
            res = db.session.query(Computer).filter(Computer.UAC_TRUSTED_FOR_DELEGATION)
            if res:
                ret = computer_list_display(res)
        else:
            res = db.session.query(EdgeLookup).filter_by(oid=nodeid).first()  # get id and typefrom sid
            if res:
                if res.otype == 'group':

                    obj = db.session.query(Group).filter_by(objectSid=res.oid).first()
                    ret = group_display(obj)
                elif res.otype == 'user':
                    obj = db.session.query(User).filter_by(objectSid=res.oid).first()
                    ret = user_display(obj)
                elif res.otype == 'machine':
                    obj = db.session.query(Computer).filter_by(objectSid=res.oid).first()
                    ret = computer_display(obj)
                elif res.otype == 'gpo':
                    obj = db.session.query(GPO).filter_by(objectGUID=res.oid).first()
                    ret = gpo_display(obj)
                elif res.otype == 'ou':
                    obj = db.session.query(Ou).filter_by(objectGUID=res.oid).first()
                    ret = ou_display(obj)
                elif res.otype == 'domain':
                    obj = db.session.query(Domain).filter_by(objectSid=res.oid).first()
                    ret = domain_display(obj)
                else:
                    print('UNKNOWN!@!!!!!!!')
        return ret
