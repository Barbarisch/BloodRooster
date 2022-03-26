import networkx as nx

from app import bloodrooster_app
from dbmodel import *


def make_node(node_id, node_name, node_type):
    print('Adding node', node_id, node_name)
    return {'id': node_id, 'name': node_name, 'type': node_type}


def make_edge(edge_id, edge_from, edge_to, edge_label):
    print('Adding edge', edge_from, edge_to, edge_label)
    return {'id': edge_id, 'from': edge_from, 'to': edge_to, 'label': edge_label}


class BloodRoostrWebApp:
    def __init__(self):
        self.db_conn = bloodrooster_app.config['SQLALCHEMY_DATABASE_URI']
        self.db_session = get_session(self.db_conn)
        self.graph = nx.DiGraph()

    def graph_update(self, json_data):
        final = {'nodes': {}, 'edges': {}}

        nodes = []
        edges = []
        ncache = []
        ecache = []

        testsid = 'S-1-5-21-3937601378-3721788405-2067139823-512'
        # nodes, edges, ncache, ecache = self.pathto(testsid, nodes, edges, ncache, ecache)
        nodes, edges, ncache, ecache = self.add_node([testsid], nodes, edges, ncache, ecache)

        idx = 0
        for node in nodes:
            final['nodes'][str(idx)] = node
            idx = idx + 1

        idx = 0
        for edge in edges:
            final['edges'][str(idx)] = edge
            idx = idx + 1

        return json.dumps(final)

    def pathto(self, sid, nodes, edges, ncache, ecache, depth=0, max_depth=5):
        """ Find paths to target sid (recursively) """
        start = self.db_session.query(EdgeLookup).filter_by(oid=sid).first()  # get id and typefrom sid
        if start:
            if start.oid not in ncache:
                ncache.append(start.oid)
                if start.otype == 'group':
                    new_node = self.db_session.query(Group).filter_by(objectSid=start.oid).first()
                    nodes.append(make_node(new_node.objectSid, new_node.name, 'group'))
                elif start.otype == 'user':
                    new_node = self.db_session.query(ADUser).filter_by(objectSid=start.oid).first()
                    nodes.append(make_node(new_node.objectSid, new_node.name, 'user'))
                elif start.otype == 'machine':
                    new_node = self.db_session.query(Machine).filter_by(objectSid=start.oid).first()
                    nodes.append(make_node(new_node.objectSid, new_node.name, 'computer'))

        if depth == max_depth:
            return nodes, edges, ncache, ecache
        # final = {'nodes': {}, 'edges': {}}
        # test = '{"nodes":{"1":{"id":"test1", "name":"FACK", "type":"computer"},"2":{"id":"test2", "name":"test2name", "type":"user"},"3":{"id":"test3", "name":"test3name", "type":"group"}},"edges":{"1":{"id":1, "from":"test1","to":"test2"},"2":{"id":2, "from":"test2","to":"test3"},"3":{"id":3, "from":"test3","to":"test1"}}}'
        # da = 'S-1-5-21-3937601378-3721788405-2067139823-512'

        # res = self.db_session.query(EdgeLookup).filter_by(oid=sid).first()  # get id from sid
        res2 = self.db_session.query(Edge).filter_by(dst=start.id)  # get edges from id
        idx = 0

        for e in res2:  # for all edges
            res = self.db_session.query(EdgeLookup).filter_by(id=e.src).first()  # get oid and otype from edge src

            # encache = []
            test = False
            # for i in ncache:
            #    if (res.oid, i) in ecache:
            #        test = True
            #        print('TESTING', i)
            #        break
                # encache.append(i[0])
                # encache.append(i[1])

            if (res.oid, start.oid) not in ecache and res.oid != start.oid:  # and res.oid not in encache:
                ecache.append((res.oid, start.oid))
                edges.append(make_edge(str(idx), res.oid, start.oid, e.label))
                idx = idx + 1
                nodes, edges, ncache, ecache = self.pathto(res.oid, nodes, edges, ncache, ecache, depth+1)
            else:
                print('not adding edge', res.oid, start.oid, e.label)

        return nodes, edges, ncache, ecache

    def add_node(self, sids, nodes, edges, ncache, ecache):
        id_sid_map = {}

        for sid in sids:
            start = self.db_session.query(EdgeLookup).filter_by(oid=sid).first()  # get id and typefrom sid
            if start:
                if start.oid not in ncache:
                    ncache.append(start.oid)
                    if start.otype == 'group':
                        new_node = self.db_session.query(Group).filter_by(objectSid=start.oid).first()
                        nodes.append(make_node(new_node.objectSid, new_node.name, 'group'))
                    elif start.otype == 'user':
                        new_node = self.db_session.query(ADUser).filter_by(objectSid=start.oid).first()
                        nodes.append(make_node(new_node.objectSid, new_node.name, 'user'))
                    elif start.otype == 'machine':
                        new_node = self.db_session.query(Machine).filter_by(objectSid=start.oid).first()
                        nodes.append(make_node(new_node.objectSid, new_node.name, 'computer'))
                    id_sid_map[start.id] = start.oid

        for node_id, node_sid in id_sid_map.items():
            nodes, edges, ncache, ecache = self.get_edges(node_id, node_sid, nodes, edges, ncache, ecache)
        return nodes, edges, ncache, ecache

    def get_edges(self, edgeid, sid, nodes, edges, ncache, ecache):
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
            nodes, edges, ncache, ecache = self.add_node(new_nodes, nodes, edges, ncache, ecache)

        return nodes, edges, ncache, ecache
