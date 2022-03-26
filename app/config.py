import os


class Config(object):
    SECRET_KEY = os.environ.get("SERET_KEY") or 'bloodrooster_webserver_secret_key'
    # SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or 'bloodrooster_webserver_secret_key'
