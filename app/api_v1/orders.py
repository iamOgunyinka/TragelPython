from datetime import datetime

from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import Date, cast

from . import v1_api as api
from .. import db
from ..decorators import paginate
from ..models import Order
from ..utils import admin_required, send_response, log_activity, date_from_string


@api.route('/orders/', methods=['GET'])
@admin_required
@paginate('orders')
def get_orders():
    today = datetime.now().date()
    date_from = date_from_string(request.args.get('from'), today)
    date_to = date_from_string(request.args.get('to'), today)
    if request.args.get("all") is not None:
        return Order.query
    return Order.query.filter(cast(Order.date_of_order, Date) >= date_from,
                              cast(Order.date_of_order, Date) <= date_to)\
        .order_by(Order.date_of_order.desc())


@api.route('/orders/<int:order_id>', methods=['GET'])
@admin_required
def get_customer_orders(order_id):
    order = Order.query.filter_by(company_id=current_user.company_id,
                                  id=order_id).first()
    if not order:
        return send_response(404, 'Order not found')
    return jsonify(order.to_json())


@api.route('/orders/', methods=['POST'])
@login_required
def new_customer_order():
    order_data = request.get_json()
    if order_data is None:
        return send_response(406, 'This request contains invalid or no data')
    payment_id, order_list = Order.import_data(order_data)
    if payment_id is None or order_list is None:
        return send_response(404, 'Missing data in order form')
    new_order = Order(staff_id=current_user.id, date_of_order=datetime.now(),
                      payment_reference=payment_id,
                      company_id=current_user.company_id, items=order_list)
    try:
        db.session.add(new_order)
        db.session.commit()
        return send_response(200, 'Order created successfully')
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[new_customer_order]', current_user.username,'',
                     str(e))
        return send_response(404, 'There was an error processing the data sent '
                                  'in your request')


@api.route('/orders/', methods=['DELETE'])
@admin_required
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
