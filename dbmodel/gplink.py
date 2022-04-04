from sqlalchemy import Column, Integer, String, ForeignKey

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class Gplink(Basemodel, Serializer):
	__tablename__ = 'gplinks'

	id = Column(Integer, primary_key=True)	
	ad_id = Column(Integer, ForeignKey('domains.id'))
	graph_id = Column(Integer, index=True)
	ou_guid = Column(String, index=True)
	gpo_uid = Column(String, index=True)

	def __init__(self, ad_id, graph_id, ou_guid, gpo_uid):
		self.ad_id = int(ad_id)
		self.graph_id = graph_id
		self.ou_guid = ou_guid
		self.gpo_uid = gpo_uid
