from flask import Flask
from flask_bootstrap import Bootstrap
from flask_session import Session
from app.config import Config
import threading
from flask_sqlalchemy import SQLAlchemy

bloodrooster_app = Flask(__name__)
bloodrooster_app.config.from_object(Config)
bloodrooster_app.sessions = {}
# bloodrooster_app.splinter_clients_mtx = threading.Lock()
Bootstrap(bloodrooster_app)
db = SQLAlchemy(bloodrooster_app)

from app.routes import *
bloodrooster_app.register_blueprint(bloodrooster_routes)
