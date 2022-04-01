from . import Basemodel, lf, dt
from sqlalchemy import Column, Integer, String, ForeignKey

from dbmodel.utils.serializer import Serializer


class Ou(Basemodel, Serializer):
	__tablename__ = 'ous'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('domains.id'))
	
	description = Column(String, index=True)
	dn = Column(String, index=True)
	gPLink = Column(String, index=True)
	name = Column(String, index=True)
	objectCategory = Column(String, index=True)
	objectClass = Column(String, index=True)
	objectGUID = Column(String, index=True)
	ou = Column(String, index=True)
	systemFlags = Column(Integer, index=True)
	whenChanged = Column(String, index=True)
	whenCreated = Column(String, index=True)
	
	def to_dict(self):
		return {
			'id': self.id,
			'ad_id': self.ad_id,
			'description': self.description,
			'guid': self.objectGUID,
			'dn': self.dn,
			'name': self.name,
			'ou': self.ou,
			'whenChanged': self.whenChanged,
			'whenCreated': self.whenCreated,
		}
	
	@staticmethod
	def from_adou(u):
		ou = Ou()
		ou.description = lf(getattr(u, 'description'))
		ou.dn = lf(getattr(u, 'distinguishedName'))
		ou.gPLink = lf(getattr(u, 'gPLink'))
		ou.name = lf(getattr(u, 'name'))
		ou.objectCategory = lf(getattr(u, 'objectCategory'))
		ou.objectClass = lf(getattr(u, 'objectClass'))
		ou.objectGUID = lf(getattr(u, 'objectGUID'))
		ou.ou = lf(getattr(u, 'ou'))
		ou.systemFlags = lf(getattr(u, 'systemFlags'))
		ou.whenChanged = dt(lf(getattr(u, 'whenChanged')))
		ou.whenCreated = dt(lf(getattr(u, 'whenCreated')))
			
		return ou
		