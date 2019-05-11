from flask import jsonify, g
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from .models import Company, User, Anonymous


auth_token = HTTPBasicAuth()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login.login_route'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


login_manager.anonymous_user = Anonymous()


@auth_token.verify_password
def verify_auth_token(token, unused):
    g.user = Company.verify_auth_token(token)
    return g.user is not None


@auth_token.error_handler
def unauthorized_token():
    response = jsonify({'status': 401, 'error': 'Unauthorized',
                        'message': 'Please send your authentication token'})
    response.status_code = 401
    return response
