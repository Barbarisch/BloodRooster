from sqlalchemy import Column, Integer, String, ForeignKey
import json

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class EdgeLookup(Basemodel, Serializer):
	__tablename__ = 'edgelookup'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('domains.id'))
	oid = Column(String, index=True)
	otype = Column(String, index=True)

	def __init__(self, ad_id, oid, otype):
		self.ad_id = int(ad_id)
		self.oid = oid
		self.otype = otype

	@staticmethod
	def from_dict(d):
		t = EdgeLookup(d['ad_id'], d['oid'], d['otype'])
		return t

	@staticmethod
	def from_json(x):
		return EdgeLookup.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id': self.ad_id,
			'oid': self.oid,
			'otype': self.otype,
		}

	def to_json(self):
		return json.dumps(self.to_dict())
