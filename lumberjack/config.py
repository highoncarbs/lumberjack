import os
import MySQLdb

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://root:alpine@127.0.0.1/lumber'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.urandom(12)
