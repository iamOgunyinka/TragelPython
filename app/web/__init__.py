from flask import Blueprint

admin = Blueprint('web', __name__)


from . import views, forms