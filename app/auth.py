from flask import jsonify, g
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager

from .utils import SUPER_USER
from .models import User, User, Anonymous

su_auth = HTTPBasicAuth()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login.login_route'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


login_manager.anonymous_user = Anonymous()


@su_auth.verify_password
def verify_password(username, password):
    g.user = User.query.filter_by(username=username).first()
    if g.user is None or g.user.role != SUPER_USER:
        return False
    return g.user.verify_password(password)


@su_auth.error_handler
def unauthorized_token():
    response = jsonify({'status': 401, 'error': 'Unauthorized',
                        'message': 'Please send a valid authentication data'})
    response.status_code = 401
    return response
