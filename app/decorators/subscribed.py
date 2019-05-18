from datetime import datetime
from functools import wraps

from flask import jsonify
from flask_login import current_user


def subscribed():
    def wrap(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not current_user:
                response = jsonify({'status': 430, 'error': 'Permission denied',
                                    'message': 'Unable to get required permission '
                                               'for this request'})
                response.status_code = 430
                return response
            if datetime.now() > max(current_user.company.subscriptions):
                response = jsonify({'status': 431, 'error': 'Permission denied',
                                    'message': 'You do not have any active '
                                               'subscription'})
                response.status_code = 431
                return response
            return function(*args, **kwargs)
        return decorated_function
    return wrap
