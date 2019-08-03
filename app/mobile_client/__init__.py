from flask import Blueprint
from flask_httpauth import HTTPBasicAuth

from ..models import User
from ..utils import send_response

mobile_api = Blueprint('mobile', __name__)


mobile_auth = HTTPBasicAuth()


@mobile_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    return user is not None and user.verify_password(password)


@mobile_auth.error_handler
def unauthorized_token():
    return send_response(401, 'Please send a valid authentication data')


from . import views
