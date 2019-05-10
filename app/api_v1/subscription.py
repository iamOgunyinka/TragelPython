from flask_login import current_user
from flask import request
from . import v1_api as api
from ..utils import admin_required, send_error, permission_required, SUPER_USER
from ..utils import date_from_string
from ..decorators import json, paginate
from ..models import Subscription, db, Company


@api.route('/subscriptions/', methods=['GET'])
@admin_required
@json
@paginate('subscriptions')
def get_subscriptions():
    return db.session.query(Subscription) \
        .filter_by(company_id=current_user.company_id).all()


@api.route('/subscribe/', methods=['POST'])
@admin_required
def add_subscription():
    token = request.json.get('key')
    company_id, date_from, date_to = Subscription.verify_auth_token(token)
    if company_id is None:
        return send_error(400, 'Bad request', 'Invalid or used token')
    if current_user.company_id != company_id:
        return send_error(401, 'Forbidden', 'Expired or unauthorized token')
    new_sub = Subscription(begin_date=date_from, end_date=date_to,
                           company_id=company_id)
    # are you trying to make use of a used token?
    if new_sub in current_user.company.subscriptions or \
            new_sub <= max(current_user.company.subscriptions):
        return send_error(402, 'Process Error', 'Unable to add this subscription')
    current_user.company.subscriptions.append(new_sub)
    db.session.add(current_user)
    db.session.commit()
    return {}, 202, {'Message': 'Successful'}


@api.route('/create_subscription', methods=['POST'])
@permission_required(SUPER_USER)
@json
def create_subscription():
    company_id = request.json.get('company_id')
    company = db.session.query(Company).filter_by(id=company_id).first()
    from_date = date_from_string(request.json.get('from'))
    to_date = date_from_string(request.json.get('to'))

    if company is None or from_date is None or to_date is None or from_date > to_date:
        return send_error(405, 'Bad request', 'No such company exist in the database')
    key = Subscription.generate_subscription_token(company_id, company.name, from_date,
                                                   to_date)
    return {}, 202, {'key': key}
