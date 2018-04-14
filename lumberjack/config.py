import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://root:alpine@127.0.0.1/lumber'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.urandom(12)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
REDIS_HOST = 'localhost'
REDIS_PASSWORD = ''
REDIS_PORT = 6379
REDIS_URL = 'redis://localhost:6379/0'

