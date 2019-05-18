from functools import wraps

from flask import jsonify
from flask_login import current_user


def permission_required(permission):
    def wrap(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if (not current_user) or (current_user.role <= permission):
                response = jsonify({'status': 430, 'error': 'Permission denied',
                                    'message': 'Unable to get required permission '
                                               'for this request'})
                response.status_code = 430
            return function(*args, **kwargs)
        return decorated_function
    return wrap
