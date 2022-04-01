from sqlalchemy import Column, Integer, String, ForeignKey

from . import Basemodel
from dbmodel.utils.serializer import Serializer


class UserSPN(Basemodel, Serializer):
	__tablename__ = 'userspn'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('domains.id'))
	owner_sid = Column(String, index=True)
	service_class = Column(String, index=True)
	computername = Column(String, index=True)
	port = Column(String, index=True)
	service_name = Column(String, index=True)

	@staticmethod
	def from_spn_str(s, user_sid=None):
		uspn = UserSPN()
		port = None
		service_name = None
		service_class, t = s.split('/', 1)
		m = t.find(':')
		if m != -1:
			computername, port = t.rsplit(':', 1)
			if port.find('/') != -1:
				port, service_name = port.rsplit('/', 1)
		else:
			computername = t
			if computername.find('/') != -1:
				computername, service_name = computername.rsplit('/', 1)

		uspn.owner_sid = user_sid
		uspn.computername = computername
		uspn.service_class = service_class
		uspn.service_name = service_name
		uspn.port = port
		return uspn


class ServiceSPN(Basemodel, Serializer):
	__tablename__ = 'servicespn'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('domains.id'))
	owner_sid = Column(String, index=True)
	service_class = Column(String, index=True)
	computername = Column(String, index=True)
	port = Column(String, index=True)
	service_name = Column(String, index=True)

	@staticmethod
	def from_spn_str(spn, owner_sid):
		port = None
		service_name = None
		service_class, t = spn.split('/', 1)
		m = t.find(':')
		if m != -1:
			computername, port = t.rsplit(':', 1)
			if port.find('/') != -1:
				port, service_name = port.rsplit('/', 1)
		else:
			computername = t
			if computername.find('/') != -1:
				computername, service_name = computername.rsplit('/', 1)

		s = ServiceSPN()
		s.owner_sid = owner_sid
		s.computername = computername
		s.service_class = service_class
		s.service_name = service_name
		if port is not None:
			s.port = str(port)
		return s

	@staticmethod
	def from_userspn(userspn):
		s = ServiceSPN()
		s.owner_sid = userspn.owner_sid
		s.computername = userspn.computername
		s.service_class = userspn.service_class
		s.service_name = userspn.service_name
		if userspn.port is not None:
			s.port = str(userspn.port)
		return s
