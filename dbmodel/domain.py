from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean
import datetime

from . import Basemodel, lf
from dbmodel.utils.serializer import Serializer


class Domain(Basemodel, Serializer):
	__tablename__ = 'domains'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	auditingPolicy = Column(String)
	creationTime = Column(DateTime)
	dc = Column(String)
	distinguishedName = Column(String)
	forceLogoff = Column(BigInteger)
	instanceType = Column(Integer)
	lockoutDuration = Column(BigInteger)
	lockOutObservationWindow = Column(BigInteger)
	lockoutThreshold = Column(Integer)
	masteredBy = Column(String)
	maxPwdAge = Column(BigInteger)
	minPwdAge = Column(BigInteger)
	minPwdLength = Column(Integer)
	name = Column(String)
	nextRid = Column(Integer)
	objectCategory = Column(String)
	objectClass = Column(String)
	objectGUID = Column(String)
	objectSid = Column(String)
	pwdHistoryLength = Column(Integer)
	pwdProperties = Column(Integer)
	serverState = Column(BigInteger)
	systemFlags = Column(BigInteger)
	uASCompat = Column(BigInteger)
	uSNChanged = Column(BigInteger)
	uSNCreated = Column(BigInteger)
	whenChanged = Column(DateTime)
	whenCreated = Column(DateTime)
	domainmodelevel = Column(Integer)
	jdversion = Column(String)
	ldap_enumeration_state = Column(String)
	smb_enumeration_state = Column(String)
	ldap_members_finished = Column(Boolean)
	ldap_sds_finished = Column(Boolean)
	edges_finished = Column(Boolean)
