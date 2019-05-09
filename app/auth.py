from flask import jsonify, g, current_app
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from .models import Company


auth_token = HTTPBasicAuth()
auth = LoginManager()
auth.session_protection = 'strong'
auth.login_view = 'login_api.login_view'


@auth_token.verify_password
def verify_auth_token(token, unused):
    g.user = Company.verify_auth_token(token)
    return g.user is not None


@auth_token.error_handler
def unauthorized_token():
    response = jsonify({'status': 401, 'error': 'unauthorized',
                        'message': 'please send your authentication token'})
    response.status_code = 401
    return response
