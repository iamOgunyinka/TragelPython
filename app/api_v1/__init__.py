from flask import Blueprint, request, jsonify
from flask_login import login_required
from ..decorators import etag, rate_limit
from ..utils import admin_required
v1_api = Blueprint('api', __name__)


@v1_api.before_request
@rate_limit(limit=5, period=15)
@admin_required
def before_request():
    """All routes in this blueprint require authentication."""
    pass


@v1_api.after_request
@etag
def after_request(rv):
    """Generate an ETag header for all routes in this blueprint."""
    return rv


from . import products, orders, items, users
