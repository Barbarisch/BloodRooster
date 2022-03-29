from flask import Flask
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
from flask_session import Session
from app.config import Config
import threading

bloodrooster_app = Flask(__name__)
bloodrooster_app.config.from_object(Config)
bloodrooster_app.sessions = {}
# bloodrooster_app.splinter_clients_mtx = threading.Lock()
Bootstrap(bloodrooster_app)
# Session(bloodrooster_app)
# bloodrooster_socketapp = SocketIO(bloodrooster_app, async_mode=None, logger=True, engineio_logger=True)

from app.routes import *
bloodrooster_app.register_blueprint(bloodrooster_routes)
