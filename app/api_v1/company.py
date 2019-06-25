from flask import request, jsonify
from flask_login import current_user

from . import v1_api as api
from .. import db
from ..decorators import paginate, permission_required
from ..models import Company
from ..utils import send_response, log_activity, sudo_required


@api.route('/companies/', methods=['GET'])
@sudo_required
@paginate('companies')
def get_companies():
    return Company.query.order_by(Company.id)


@api.route('/companies/<int:company_id>', methods=['GET'])
@sudo_required
def get_company(company_id):
    return Company.query.get_or_404(company_id)


@api.route('/companies', methods=['POST'])
@sudo_required
def create_new_company():
    company = Company.import_json(request.json)
    if company is None:
        return send_response(404, 'Bad request', 'Unable to get the JSON data needed')
    db.session.add(company)
    db.session.commit()

    return send_response(200, 'Successful', 'Successful')


@api.route('/companies/<int:company_id>', methods=['DELETE'])
@sudo_required
def delete_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return send_response(404, 'Company not found', '')
    db.session.delete(company)
    db.session.commit()
    log_activity('DELETE[delete_company]', current_user.username, company.name, '')
    return send_response(200, 'Successful', 'OK')
