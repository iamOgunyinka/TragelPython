from flask import Blueprint
from ..decorators import rate_limit


login_api = Blueprint('login', __name__)


@login_api.before_request
@rate_limit(3, 15)
def before_any_request():
    pass