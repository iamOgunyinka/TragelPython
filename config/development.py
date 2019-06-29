import os

basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
IGNORE_AUTH = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'tragel.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'top-secret-key'
