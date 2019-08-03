from flask import Blueprint

web_admin = Blueprint('web', __name__)


from . import views, forms