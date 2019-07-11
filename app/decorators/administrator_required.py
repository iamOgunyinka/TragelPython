from functools import wraps

from flask import jsonify, render_template
from flask_login import current_user


class UserType:
    BasicUser = 0x4A
    Administrator = 0x4B
    SuperUser = 0x4C


def role_to_string(role):
    if role == UserType.SuperUser:
        return "Super User"
    elif role == UserType.Administrator:
        return "Administrator"
    else:
        return "Basic User"


def permission_required(permission):
    def wrap(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if current_user is None or (current_user.role < permission):
                response = jsonify({'status_code': 402,
                                    'message': 'Permission denied',
                                    'status': 'This request is only allowed '
                                              'for an administrator'})
                response.status_code = 402
                return response
            return function(*args, **kwargs)
        return decorated_function
    return wrap


def sudo_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user is None or (current_user.role != UserType.SuperUser):
            return render_template('error.html')
        return function(*args, **kwargs)
    return decorated_function
