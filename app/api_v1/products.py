from flask import request
from flask_login import login_required
from . import v1_api as api
from .. import db
from ..models import Product
from ..decorators import json, paginate
from ..utils import admin_required


@api.route('/products/', methods=['GET'])
@login_required
@json
@paginate('products')
def get_products():
    return Product.query


@api.route('/products/<int:id>', methods=['GET'])
@login_required
@json
def get_product(product_id):
    return Product.query.get_or_404(product_id)


@api.route('/products/<int:id>', methods=['PUT'])
@admin_required
@json
def edit_product(id):
    product = Product.query.get_or_404(id)
    product.import_data(request.json)
    db.session.add(product)
    db.session.commit()
    return {}


@api.route('/products/', methods=['POST'])
@admin_required
@json
def new_product():
    product = Product()
    product.import_data(request.json)
    db.session.add(product)
    db.session.commit()
    return {}, 201, {'Location': product.get_url()}
