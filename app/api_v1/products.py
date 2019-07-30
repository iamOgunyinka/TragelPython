from flask import request, jsonify
from flask_login import login_required, current_user

from . import v1_api as api
from .. import db
from ..decorators import paginate, UserType, permission_required, \
    fully_subscribed
from ..models import Product
from ..utils import send_response, log_activity


@api.route('/products/', methods=['GET'])
@login_required
@paginate('products')
def get_products():
    return Product.query.filter_by(company_id=current_user.company_id)\
        .order_by(Product.id)


@api.route('/get_products/<int:company_id>', methods=['GET'])
@login_required
def get_company_products(company_id):
    return Product.query.filter_by(company_id=company_id).order_by(
        Product.name).all()


@api.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    product = Product.query.get(product_id)
    return jsonify(product.to_json()) if product \
        else send_response(404, 'Product not found')


@api.route('/products/', methods=['POST'])
@permission_required(UserType.Administrator)
@fully_subscribed
def new_product():
    try:
        items = Product.from_json(request.get_json(), current_user.company_id)
        db.session.add_all(items)
        db.session.commit()
    except ValueError as v_e:
        return send_response(400, str(v_e))
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[new_products]', current_user.username, [],
                     str(e))
        return send_response(403, 'Unable to add products')
    return send_response(200, 'Products added')


@api.route('/products/', methods=['DELETE'])
@permission_required(UserType.Administrator)
@fully_subscribed
def delete_product():
    product_id = request.args.get('product_id', 0, type=int)
    reason = request.args.get('reason', '')
    product = Product.query.filter_by(company_id=current_user.company_id,
                                      id=product_id).first()
    if product is not None:
        product.deleted = True
        db.session.commit()
        log_activity('DELETION[products]', current_user.username,
                     current_user.company_id, reason)
        return send_response(200, 'Successful')
    return send_response(404, 'There was an error processing the data sent in '
                              'your request')


@api.route('/stock', methods=['POST'])
@permission_required(UserType.Administrator)
@fully_subscribed
def add_stock():
    return jsonify({})
