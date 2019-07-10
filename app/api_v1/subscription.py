from flask import request
from flask_login import current_user

from . import v1_api as api
from ..decorators import paginate, UserType, permission_required
from ..models import Subscription, db
from ..utils import send_response


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
    company_id, date_from, date_to = data
    ex_token = Subscription.query.filter_by(company_id=company_id, token=token)
    if current_user.company_id != company_id or ex_token.first() is not None:
        return send_response(401, 'Forbidden', 'Expired or unauthorized token')
    new_sub = Subscription(begin_date=date_from, end_date=date_to,
                           company_id=company_id, token=token)
    # are you trying to make use of an old token?
    last_subscription = Subscription.query.filter_by(
        company_id=company_id).order_by(Subscription.id.desc()).first()
    if last_subscription and new_sub <= last_subscription:
        return send_response(402, 'Unable to add this subscription')
    current_user.company.subscriptions.append(new_sub)
    db.session.add(current_user)
    db.session.add(new_sub)
    db.session.commit()
    return send_response(200, 'Successful')
