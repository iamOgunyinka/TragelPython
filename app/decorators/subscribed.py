from functools import wraps
from flask_login import current_user
from flask import jsonify
from ..models import Subscription, User


def subscribed():
    def wrap(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not current_user:
                response = jsonify({'status': 430, 'error': 'Permission denied',
                                    'message': 'Unable to get required permission '
                                               'for this request'})
                response.status_code = 430
            if current_user.company.subscriptions
            return function(*args, **kwargs)
        return decorated_function
    return wrap
