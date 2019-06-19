from flask import request, jsonify
from flask_login import login_required, current_user

from . import v1_api as api
from .. import db
from ..decorators import paginate
from ..models import Product
from ..utils import admin_required, send_response, log_activity


@api.route('/products/', methods=['GET'])
@admin_required
@paginate('products')
def get_products():
    return db.session.query(Product).filter_by(company_id=current_user.company_id)\
        .order_by(Product.id)


@api.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id).first()
    return jsonify(product.to_json()) if product else send_response(404, 'Product not found')


@api.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
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
        return send_response(402, 'An exception occurred with your request')
    return send_response(200, 'OK')


@api.route('/products/', methods=['POST'])
@admin_required
def new_product():
    items = Product.from_json(request.get_json(), current_user.company_id)
    if items is None:
        return send_response(417, 'There are some missing data in the request')
    try:
        db.session.add_all(items)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[new_products]', current_user.username, [items], str(e))
        return send_response(403, 'Unable to add products')
    return send_response(200, 'Products added')
