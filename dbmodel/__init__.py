from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import enum
import logging

Basemodel = declarative_base()


def windowed_query(q, column, windowsize, is_single_entity=True):
	""" Break a Query into chunks on a given column. """

	# single_entity = q.is_single_entity
	q = q.add_column(column).order_by(column)
	last_id = None

	while True:
		subq = q
		if last_id is not None:
			subq = subq.filter(column > last_id)
		chunk = subq.limit(windowsize).all()
		if not chunk:
			break
		last_id = chunk[-1][-1]
		for row in chunk:
			if is_single_entity is True:
				yield row[0]
			else:
				yield row[0:-1]


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
	"""
	This function runs after the sqlite connection is made, and speeds up the insert operations considerably
	Sadly I could not find a way to limit the execution to sqlite so other DBs will trow an error :(
	TODO: fix this
	"""
	cursor = dbapi_connection.cursor()
	cursor.execute("PRAGMA journal_mode = MEMORY")
	cursor.execute("PRAGMA synchronous = OFF")
	cursor.execute("PRAGMA temp_store = MEMORY")
	cursor.execute("PRAGMA cache_size = 500000")
	cursor.close()


def lf(x, sep=','):
	"""
	flattens objects
	"""
	if x is None:
		return x
	if isinstance(x, list):
		return sep.join(x)
	elif isinstance(x, (datetime.datetime, int, enum.IntFlag)):
		return x
	return str(x)


def dt(x):
	"""
	datetime corrections
	"""
	if x in ['', None, 'None']:
		return None
	if isinstance(x, str):
		return datetime.datetime.fromisoformat(x)
	if not isinstance(x, datetime.datetime):
		print(x)
	return x


def bc(x):
	"""
	boolean corrections
	"""
	if x is None:
		return None
	if isinstance(x, bool):
		return x
	if isinstance(x, str):
		if x.upper() == 'TRUE':
			return True
		elif x.upper() == 'FALSE':
			return False
		elif x.upper() == 'NONE':
			return None
	raise Exception('Cant convert this to bool: %s type: %s' % (x, type(x)))


from .domain import *
from .group import *
from .computer import *
from .user import *
from .ou import *
from .gpo import *
from .container import *
from .gplink import *
from .trust import *
from .spn import *
from .ace import Ace
from .member import Member
from .childobject import ChildObject
from .session import Session
from .edge import Edge
from .edgelookup import EdgeLookup

# TODO come back to these
# from .netsession import *
# from .netshare import *
# from .localgroup import *
# from .delegation import *
# from .rdnslookup import RDNSLookup
# from .dnslookup import DNSLookup
# from .schemaentry import ADSchemaEntry


def create_db(connection, verbosity=0, inmemory=False):
	logging.info('Creating database %s' % connection)
	engine = create_engine(connection, echo=True if verbosity > 1 else False)  # 'sqlite:///dump.db'
	Basemodel.metadata.create_all(engine)
	session_maker = sessionmaker(engine)
	new_session = None
	try:
		new_session = session_maker()
		if inmemory is True:
			return session

	finally:
		if inmemory is False and new_session:
			new_session.close()
	logging.info(f'Done creating database {connection}')


def get_session(connection, verbosity=0):
	logging.debug('Connecting to DB')
	engine = create_engine(connection, echo=True if verbosity > 1 else False)

	# create a configured "session_maker" class
	logging.debug('Creating session')
	session_maker = sessionmaker(bind=engine)

	# create a Session
	return session_maker()
