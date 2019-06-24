from functools import wraps

from flask import jsonify
from flask_login import current_user


def permission_required(permission):
    def wrap(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if (current_user is None) or (current_user.role < permission):
                response = jsonify({'status_code': 4012,
                                    'message': 'Permission denied',
                                    'status': 'Unable to get required permission for '
                                              'this request'})
                response.status_code = 402
                return response
            return function(*args, **kwargs)
        return decorated_function
    return wrap
