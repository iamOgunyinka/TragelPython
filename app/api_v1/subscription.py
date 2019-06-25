from datetime import datetime

from flask import request
from flask_login import current_user

from . import v1_api as api
from ..decorators import paginate
from ..models import Subscription, db, Company
from ..utils import admin_required, send_response, sudo_required
from ..utils import date_from_string


@api.route('/subscriptions/', methods=['GET'])
@admin_required
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
        return send_response(400, 'Invalid or used token')
    if current_user.company_id != company_id:
        return send_response(401, 'Forbidden', 'Expired or unauthorized token')
    new_sub = Subscription(begin_date=date_from, end_date=date_to,
                           company_id=company_id)
    # are you trying to make use of a used token?
    if new_sub in current_user.company.subscriptions or \
            new_sub <= max(current_user.company.subscriptions):
        return send_response(402, 'Unable to add this subscription')
    current_user.company.subscriptions.append(new_sub)
    db.session.add(current_user)
    db.session.commit()
    return send_response(200, 'Successful')


@api.route('/create_subscription', methods=['POST'])
@sudo_required
def create_subscription():
    company_id = request.json.get('company_id')
    company = db.session.query(Company).filter_by(id=company_id).first()
    from_date = date_from_string(request.json.get('from'), datetime.now().date())
    to_date = date_from_string(request.json.get('to'), datetime.now().date())

    if company is None or from_date is None or to_date is None or from_date > to_date:
        return send_response(405, 'No such company exist in the database')
    key = Subscription.generate_subscription_token(company_id, company.name, from_date,
                                                   to_date)
    return send_response(200, key)
