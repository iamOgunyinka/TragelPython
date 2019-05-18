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
    return db.session.query(Product).filter_by(current_user.company_id).all()


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
                                                  company_id=current_user.company_id)
    try:
        product_name = request.json.get('name')
        product_price = request.json.get('price')
        product.name = product_name if product_name is not None else product.name
        product.price = product_price if product_price is not None else product.price
        db.session.add(product)
        db.session.commit()
    except Exception as e:
        log_activity('EXCEPTION[edit_product]', current_user.username, '', str(e))
        return send_error(402, 'Bad request', 'An exception occurred with your request')
    return {}


@api.route('/products/', methods=['POST'])
@admin_required
@json
def new_product():
    product_name, product_price = Product.from_json(request.get_json())
    if product_name is None or product_price is None:
        return send_error(400, 'Missing data',
                          'There are some missing data in the request')
    product = Product(name=product_name, price=product_price)
    db.session.add(product)
    db.session.commit()
    return {}, 201, {'Location': product.get_url()}
