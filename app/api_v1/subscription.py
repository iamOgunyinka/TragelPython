from datetime import datetime

from flask import request
from flask_login import current_user

from . import v1_api as api
from ..decorators import paginate, sudo_required, UserType, permission_required
from ..models import Subscription, db, Company
from ..utils import date_from_string
from ..utils import send_response


@api.route('/subscriptions/', methods=['GET'])
@permission_required(UserType.Administrator)
@paginate('subscriptions')
def get_subscriptions():
    return Subscription.query.filter_by(company_id=current_user.company_id).all()


@api.route('/subscribe/', methods=['POST'])
@permission_required(UserType.Administrator)
def add_subscription():
    token = request.json.get('key')
    data = Subscription.verify_auth_token(token)
    if data is None:
        return send_response(400, 'Invalid or used token')
    company_id, date_from, date_to = data
    ex_token = Subscription.query.filter_by(company_id=company_id, token=token)
    if current_user.company_id != company_id or ex_token.first() is not None:
        return send_response(401, 'Forbidden', 'Expired or unauthorized token')
    new_sub = Subscription(begin_date=date_from, end_date=date_to,
                           company_id=company_id, token=token)
    # are you trying to make use of an old token?
    if new_sub <= max(current_user.company.subscriptions):
        return send_response(402, 'Unable to add this subscription')
    current_user.company.subscriptions.append(new_sub)
    db.session.add(current_user)
    db.session(new_sub)
    db.session.commit()
    return send_response(200, 'Successful')


@api.route('/create_subscription', methods=['POST'])
@sudo_required
def create_subscription():
    company_id = request.json.get('company_id', 0, type=int)
    now = datetime.now().date()
    from_date = date_from_string(request.json.get('from'), now)
    to_date = date_from_string(request.json.get('to'), now)

    company = Company.query.filter_by(id=company_id).first()
    if from_date >= to_date or company is None:
        return send_response(405, 'Invalid transaction initiated')
    key = Subscription.generate_subscription_token(company_id, company.name,
                                                   from_date, to_date)
    return send_response(200, key)
