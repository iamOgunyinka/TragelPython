from flask import request
from flask_login import current_user

from . import v1_api as api
from ..decorators import paginate, UserType, permission_required
from ..models import Subscription, db
from ..utils import send_response
from datetime import datetime


@api.route('/subscriptions/', methods=['GET'])
@permission_required(UserType.Administrator)
@paginate('subscriptions')
def get_subscriptions():
    return Subscription.query.filter_by(
        company_id=current_user.company_id).order_by(Subscription.id.asc())


@api.route('/subscribe/', methods=['POST'])
@permission_required(UserType.Administrator)
def add_subscription():
    token = request.json.get('key')
    data = Subscription.verify_auth_token(token)
    if data is None:
        return send_response(400, 'Invalid or used token')
    company_name, date_from, date_to = data
    ex_token = Subscription.query.filter_by(token=token).first()
    if (current_user.company.name != company_name) or ex_token:
        return send_response(401, 'Invalid or used token')
    start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    print(start_date, end_date)

    new_sub = Subscription(begin_date=start_date, end_date=end_date,
                           company_id=current_user.company_id, token=token)
    current_user.company.subscription_active = True
    db.session.add(current_user.company)
    db.session.add(new_sub)
    db.session.commit()
    return send_response(200, 'Successful')


@api.route('/expiry', methods=['GET'])
@permission_required(UserType.Administrator)
def get_expiration():
    last_sub = Subscription.query.filter_by(company_id=current_user.company_id)\
        .order_by(Subscription.id.desc()).first()
    if not last_sub:
        return send_response(200, 'No subscriptions has been made yet')
    return send_response(200, last_sub.end_date.date().isoformat())
