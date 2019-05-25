from datetime import datetime

from flask import request
from flask_login import login_required, current_user

from . import v1_api as api
from .. import db
from ..decorators import json, paginate
from ..models import Order
from ..utils import admin_required, send_error, log_activity, date_from_string


@api.route('/orders/', methods=['GET'])
@json
@admin_required
@paginate('orders')
def get_orders():
    date_to_use = date_from_string(request.args.get('date'))
    date_from = date_from_string(request.args.get('from'))
    date_to = date_from_string(request.args.get('to'))

    if date_from is None or date_to is None:
        if date_to_use is None:
            return db.session.query(Order)\
                .filter_by(company_id=current_user.company_id).all()
        else:
            return Order.query.filter_by(date_of_order=date_to_use,
                                         company_id=current_user.company_id).all()
    else:
        return Order.query.filter(Order.date_of_order >= date_from,
                                  Order.date_of_order <= date_to).all()


@api.route('/orders/<int:order_id>', methods=['GET'])
@json
@admin_required
def get_customer_orders(order_id):
    return db.session.query(Order).filter_by(company_id=current_user.company_id,
                                             id=order_id).first()


@api.route('/create_order', methods=['POST'])
@login_required
@json
def new_customer_order():
    order_data = request.get_json()
    if order_data is None:
        return send_error(400, 'Bad request', 'This request contains invalid or no data')
    payment_id, order_object = Order.import_data(order_data)
    if payment_id is None or order_object is None:
        return send_error(400, 'Bad request', 'Missing data in order form')
    new_order = Order(staff_id=current_user.id, date_of_order=datetime.now(),
                      payment_reference=payment_id,
                      company_id=current_user.company_id, items=order_object)
    try:
        db.session.add(new_order)
        db.session.commit()
        return {}, 201, {'Message': 'Successful'}
    except Exception as e:
        log_activity('EXCEPTION[new_customer_order]', current_user.username,'',
                     str(e))
        return send_error(404, 'Bad request', 'There was an error processing '
                                              'the data sent in your request')


@api.route('/orders/<int:order_id>', methods=['DELETE'])
@admin_required
@json
def delete_order(order_id):
    order = db.session.query(Order).filter_by(company_id=current_user.company_id,
                                              id=order_id).first()
    if order is not None:
        db.session.delete(order)
        db.session.commit()
        return {}
    return send_error(404, 'Bad request',
                      'There was an error processing the data sent in your request')
