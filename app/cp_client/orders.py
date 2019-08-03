import base64
from datetime import datetime

from flask import request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import Date, cast

from . import v1_api as api
from .. import db
from ..decorators import paginate, permission_required, UserType, fully_subscribed
from ..models import Order, User, Confirmation
from ..utils import send_response, log_activity, \
    date_from_string, SearchType, PaymentType


@api.route('/orders/', methods=['GET'])
@permission_required(UserType.Administrator)
@paginate('orders')
@fully_subscribed
def get_orders():
    date_from = date_from_string(request.args.get('from'), None)
    date_to = date_from_string(request.args.get('to'), None)

    cast_date_from, cast_date_to = None, None
    if date_from and date_to:
        cast_date_from = cast(Order.date_of_order, Date)
        cast_date_to = cast(Order.date_of_order, Date)
    query = Order.query.filter_by(company_id=current_user.company_id)
    if request.args.get('all'):
        return query.order_by(Order.date_of_order.desc())
    elif request.args.get('search_type'):
        search_type = request.args.get('search_type', 0, type=int)
        if search_type in (SearchType.BY_PAYMENT_REF, SearchType.BY_CASH_PAYMENT):
            payment_reference_id = request.args.get('ref_id')
            if date_from is None or date_to is None:
                return query.filter_by(payment_reference=payment_reference_id)\
                    .order_by(Order.date_of_order.desc())
            else:
                query = query.filter(cast_date_from >= date_from,
                                     cast_date_to <= date_to)
                if payment_reference_id != 'cash':
                    return query.filter_by(payment_reference=payment_reference_id)\
                        .order_by(Order.date_of_order.desc())
                return query.filter_by(payment_type=PaymentType.Cash)\
                    .order_by(Order.date_of_order.desc())
        elif search_type in (SearchType.BY_PUBLIC_USER, SearchType.BY_COMPANY_USER):
            username = request.args.get('username')
            user = User.query.filter_by(username=username).first()
            if not user:
                abort(400)
            query = query.filter_by(staff_id=user.id)
            if not any((date_from, date_to)):
                return query.order_by(Order.date_of_order.desc())
            else:
                return query.filter(cast_date_from >= date_from,
                                    cast_date_to <= date_to)\
                    .order_by(Order.date_of_order.desc())
    return query.filter(cast_date_from >= date_from, cast_date_to <= date_to)\
        .order_by(Order.date_of_order.desc())


@api.route('/orders/<int:order_id>', methods=['GET'])
@permission_required(UserType.Administrator)
@fully_subscribed
def get_customer_orders(order_id):
    order = Order.query.filter_by(company_id=current_user.company_id,
                                  id=order_id).first()
    if not order:
        return send_response(404, 'Order not found')
    return jsonify(order.to_json())


@api.route('/orders/confirm', methods=['GET'])
@permission_required(UserType.Administrator)
@fully_subscribed
def confirm_customer_order():
    details = base64.b64decode(request.args.get('payload')).decode()
    order_id, confirmation_date = details.split('@')
    # confirmation_date is in ISO standard format
    try:
        confirmation_date = datetime.strptime(confirmation_date,
                                              '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        confirmation_date = datetime.now().isoformat()
    order = Order.query.get(int(order_id))
    if order is None:
        return send_response(403, 'Unable to find the order specified')
    order.payment_confirmed = Confirmation(confirmed=True, admin_id=current_user.id,
                                           date=confirmation_date)
    db.session.add(order)
    db.session.commit()
    return send_response(200, order.payment_confirmed.to_json() )


@api.route('/orders/count', methods=['GET'])
@permission_required(UserType.Administrator)
@fully_subscribed
def order_count():
    count = Order.query.filter_by(company_id=current_user.company_id).count()
    return send_response(200, {'count': count})


@api.route('/orders/', methods=['POST'])
@login_required
def new_customer_order():
    order_data = request.get_json()
    if order_data is None:
        return send_response(406, 'This request contains invalid or no data')
    result_tuple = Order.import_data(order_data)
    if not result_tuple:
        return send_response(404, 'Missing data in order form')
    payment_id, payment_method, order_list = result_tuple
    new_order = Order(staff_id=current_user.id, date_of_order=datetime.now(),
                      payment_reference=payment_id, payment_type=payment_method,
                      company_id=current_user.company_id, items=order_list)
    try:
        db.session.add(new_order)
        db.session.commit()
        return send_response(200, 'Order created successfully')
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[new_customer_order]', current_user.username, '',
                     str(e))
        return send_response(404, 'There was an error processing the data sent '
                                  'in your request')


@api.route('/orders/', methods=['DELETE'])
@permission_required(UserType.Administrator)
@fully_subscribed
def delete_order():
    order_id = request.args.get('order_id', 0)
    reason = request.args.get('reason', '')
    order = Order.query.filter_by(company_id=current_user.company_id,
                                  id=order_id).first()
    if order is not None:
        order.deleted = True
        db.session.commit()
        log_activity('DELETION[orders]', current_user.username,
                     current_user.company_id, reason)
        return send_response(200, 'Successful')
    return send_response(404, 'There was an error processing the data sent in '
                              'your request')
