import os

DEBUG = True
IGNORE_AUTH = True
SECRET_KEY = ''
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
