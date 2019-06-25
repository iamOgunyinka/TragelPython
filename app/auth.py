from flask import g
from flask_httpauth import HTTPBasicAuth

from .models import User
from .utils import UserType, send_response

su_auth = HTTPBasicAuth()


@su_auth.verify_password
def verify_password(username, password):
    g.user = User.query.filter_by(username=username).first()
    if g.user is None or g.user.role != UserType.SuperUser:
        return False
    return g.user.verify_password(password)


@su_auth.error_handler
def unauthorized_token():
    return send_response(401, 'Please send a valid authentication data')
