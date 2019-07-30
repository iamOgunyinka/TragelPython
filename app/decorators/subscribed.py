from functools import wraps

from flask_login import current_user

from ..utils import send_response


def fully_subscribed(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not current_user:
            return send_response(401, 'Unable to get required permission for '
                                      'this request')
        if current_user.company is None or \
                not current_user.company.subscription_active:
            return send_response(401, 'You do not have any active subscription')
        return function(*args, **kwargs)
    return decorated_function
