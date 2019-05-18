from flask import request
from flask_login import current_user

from . import v1_api as api
from .. import db
from ..decorators import json, paginate, permission_required
from ..models import Company
from ..utils import send_error, log_activity, SUPER_USER


@api.route('/companies/', methods=['GET'])
@json
@permission_required(SUPER_USER)
@paginate('companies')
def get_companies():
    return Company.query


@api.route('/companies/<int:company_id>', methods=['GET'])
@permission_required(SUPER_USER)
@json
def get_company(company_id):
    return Company.query.get_or_404(company_id)


@api.route('/companies', methods=['POST'])
@permission_required(SUPER_USER)
@json
def create_new_company():
    company = Company.import_json(request.json)
    if company is None:
        return send_error(404, 'Bad request', 'Unable to get the JSON data needed')
    db.session.add(company)
    db.session.commit()
    return {}, 202, {'Message': 'Successful'}


@api.route('/companies/<int:company_id>', methods=['DELETE'])
@permission_required(SUPER_USER)
@json
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    log_activity('DELETE[delete_company]', current_user.username, company.name, '')
    db.session.delete(company)
    db.session.commit()
    return {}
