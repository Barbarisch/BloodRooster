from sqlalchemy import Column, Integer, String, ForeignKey
import json

from . import Basemodel
from dbmodel.utils.serializer import Serializer


# TODO update this
class Session(Basemodel, Serializer):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    ad_id = Column(Integer, ForeignKey('domains.id'))
    src_sid = Column(String)
    dst_sid = Column(String)
    label = Column(String, index=True)

    def __init__(self, ad_id, src, dst, label):
        self.ad_id = int(ad_id)
        self.src_sid = src
        self.dst_sid = dst
        self.label = label

    @staticmethod
    def from_dict(d):
        return Session(d['ad_id'], d['src_sid'], d['dst_sid'], d['label'])

    @staticmethod
    def from_json(x):
        return Session.from_dict(json.loads(x))

    def to_dict(self):
        return {
            'ad_id': self.ad_id,
            'src': self.src_sid,
            'dst': self.dst_sid,
            'label': self.label
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_csv_line(line):
        row = line.split(',')
        return Session(int(row[1]), int(row[2]), int(row[3]), int(row[4]))
