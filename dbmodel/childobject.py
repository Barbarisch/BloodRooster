from sqlalchemy import Column, Integer, String, ForeignKey
import json

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class ChildObject(Basemodel, Serializer):
    __tablename__ = 'childobjects'

    id = Column(Integer, primary_key=True)
    ad_id = Column(Integer, ForeignKey('domains.id'))
    graph_id = Column(Integer, index=True)
    container_id = Column(String)
    child_id = Column(String)
    child_type = Column(String, index=True)

    def __init__(self, ad_id, graph_id, src, dst, child_type):
        self.ad_id = int(ad_id)
        self.graph_id = graph_id
        self.container_id = src
        self.child_id = dst
        self.child_type = child_type

    @staticmethod
    def from_dict(d):
        return ChildObject(d['ad_id'], d['graph_id'], d['container_id'], d['child_id'], d['child_type'])

    @staticmethod
    def from_json(x):
        return ChildObject.from_dict(json.loads(x))

    def to_dict(self):
        return {
            'ad_id': self.ad_id,
            'graph_id': self.graph_id,
            'container_id': self.container_id,
            'child_id': self.child_id,
            'child_type': self.child_type
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_csv_line(line):
        row = line.split(',')
        return ChildObject(int(row[1]), int(row[2]), int(row[3]), int(row[4]), row[5])
