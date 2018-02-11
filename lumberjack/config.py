import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'jack.sqlite')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.urandom(12)
