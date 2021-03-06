from sqlalchemy import Column, Integer, String, ForeignKey
import json

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class Edge(Basemodel, Serializer):
	__tablename__ = 'edges'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('domains.id'))
	src = Column(Integer, index=True)
	dst = Column(Integer, index=True)
	label = Column(String, index=True)

	def __init__(self, ad_id, src, dst, label):
		self.ad_id = int(ad_id)
		self.src = int(src)
		self.dst = int(dst)
		self.label = label

	@staticmethod
	def from_dict(d):
		return Edge(d['ad_id'], d['src'], d['dst'], d['label'])

	@staticmethod
	def from_json(x):
		return Edge.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id': self.ad_id,
			'src': self.src,
			'dst': self.dst,
			'label': self.label
		}

	def to_json(self):
		return json.dumps(self.to_dict())

	@staticmethod
	def from_csv_line(line):
		row = line.split(',')
		return Edge(int(row[1]), int(row[2]), int(row[3]), int(row[4]), row[5])
