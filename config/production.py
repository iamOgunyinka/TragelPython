import os

DEBUG = False
SECRET_KEY = ''
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')