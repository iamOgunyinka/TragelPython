from flask import jsonify, g
from flask_httpauth import HTTPBasicAuth
from .utils import SUPER_USER
from .models import User

su_auth = HTTPBasicAuth()


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
