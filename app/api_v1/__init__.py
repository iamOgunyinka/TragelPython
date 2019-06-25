from flask import Blueprint
from flask_uploads import IMAGES, UploadSet
from ..decorators import etag, rate_limit
from ..utils import send_response

v1_api = Blueprint('api', __name__)
images = UploadSet('photos', IMAGES)


@v1_api.before_request
@rate_limit(limit=5, period=15)
def before_request():
    """All routes in this blueprint require authentication."""
    pass


@v1_api.app_errorhandler(404)
def app_err_handler(e):
    return send_response(404, str(e))


@v1_api.after_request
@etag
def after_request(rv):
    """Generate an ETag header for all routes in this blueprint."""
    return rv


from . import products, orders, users, company, subscription, uploads
