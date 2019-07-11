from datetime import datetime
from functools import wraps

from flask import jsonify
from flask_login import current_user

from ..models import Subscription


def fully_subscribed(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not current_user:
            response = jsonify({'status': 401, 'error': 'Permission denied',
                                'message': 'Unable to get required permission '
                                           'for this request'})
            response.status_code = 401
            return response
        last_subscription = Subscription.query.filter_by(
            company_id=current_user.company_id).order_by(
            Subscription.id.desc()).first()
        expired = last_subscription is None or \
                  last_subscription.end_date.date() < datetime.utcnow().date()
        if expired:
            response = jsonify({'status': 401, 'error': 'Permission denied',
                                'message': 'You do not have any active '
                                           'subscription'})
            response.status_code = 401
            return response
        return function(*args, **kwargs)
    return decorated_function
