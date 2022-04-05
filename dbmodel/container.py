from sqlalchemy import Column, Integer, String, ForeignKey

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class Container(Basemodel, Serializer):
    __tablename__ = 'containers'

    id = Column(Integer, primary_key=True)
    ad_id = Column(Integer, ForeignKey('domains.id'))
    name = Column(String)
    dn = Column(String)
    objectGUID = Column(String, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'ad_id': self.ad_id,
            'name': self.name,
            'dn': self.dn,
            'guid': self.objectGUID,
        }
