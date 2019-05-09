from flask import request
from flask_login import login_required, current_user
from . import v1_api as api
from .. import db
from ..models import Order
from ..decorators import json, paginate
from ..utils import admin_required


@api.route('/orders/', methods=['GET'])
@json
@admin_required
@paginate('orders')
def get_orders():
    return db.session.query(Order).filter_by(company_id=current_user.company_id).all()


@api.route('/orders/<int:id>', methods=['GET'])
@json
@admin_required
def get_customer_orders(order_id):
    return db.session.query(Order).filter_by(company_id=current_user.company_id,
                                             id=order_id).first()


@api.route('/create_order', methods=['POST'])
@login_required
@json
def new_customer_order():

    customer = Customer.query.get_or_404(id)
    order = Order(customer=customer)
    order.import_data(request.json)
    db.session.add(order)
    db.session.commit()
    return {}, 201, {'Location': order.get_url()}


@api.route('/orders/<int:id>', methods=['PUT'])
@json
def edit_order(id):
    order = Order.query.get_or_404(id)
    order.import_data(request.json)
    db.session.add(order)
    db.session.commit()
    return {}


@api.route('/orders/<int:id>', methods=['DELETE'])
@json
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return {}
