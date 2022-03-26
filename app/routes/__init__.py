from flask import Blueprint
bloodrooster_routes = Blueprint('routes', __name__)

from .routes import *
from .websockets import *
