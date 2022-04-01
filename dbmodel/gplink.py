from sqlalchemy import Column, Integer, String

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class Gplink(Basemodel, Serializer):
	__tablename__ = 'gplinks'

	id = Column(Integer, primary_key=True)	
	ad_id = Column(Integer, index=True)
	ou_guid = Column(String, index=True)
	gpo_dn = Column(String, index=True)
	order = Column(Integer, index=True)
