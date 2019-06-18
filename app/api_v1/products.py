from flask import request
from flask_login import login_required, current_user

from . import v1_api as api
from .. import db
from ..decorators import json, paginate
from ..models import Product
from ..utils import admin_required, send_error, log_activity


@api.route('/products/', methods=['GET'])
@admin_required
@json
@paginate('products')
def get_products():
    return db.session.query(Product).filter_by(company_id=current_user.company_id)\
        .order_by(Product.id)


@api.route('/products/<int:product_id>', methods=['GET'])
@login_required
@json
def get_product(product_id):
    return Product.query.get_or_404(product_id)


@api.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
@json
def edit_product(product_id):
    product = db.session.query(Product).filter_by(id=product_id,
                                                  company_id=current_user.company_id)\
        .first()
    product_name = request.json.get('name')
    product_price = request.json.get('price')
    product.name = product_name if product_name is not None else product.name
    product.price = product_price if product_price is not None else product.price
    try:
        db.session.add(product)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[edit_product]', current_user.username, '', str(e))
        return send_error(402, 'Bad request', 'An exception occurred with your request')
    return {'status': 'OK'}, 200, {}


@api.route('/products/', methods=['POST'])
@admin_required
@json
def new_product():
    items = Product.from_json(request.get_json(), current_user.company_id)
    if items is None:
        return send_error(400, 'Missing data',
                          'There are some missing data in the request')
    print(items)
    try:
        db.session.add_all(items)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[new_products]', current_user.username, [items], str(e))
        return send_error(403, 'Database error', 'Unable to add products')
    return {'status': 'OK'}, 201, {}
