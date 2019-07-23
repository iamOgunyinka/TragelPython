import json

from flask import request
from flask_login import current_user, login_required

from . import v1_api as api
from .. import db
from ..decorators import paginate, sudo_required
from ..models import Company, State, City
from ..utils import send_response, log_activity, tragel_companies_tag, \
    data_cache


@api.route('/companies/', methods=['GET'])
@paginate('companies')
@sudo_required
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
        return send_response(404, 'Bad request',
                             'Unable to get the JSON data needed')
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
    log_activity('DELETE[delete_company]', current_user.username,
                 company.name, '')
    return send_response(200, 'Successful', 'OK')


@api.route('/get_companies', methods=['GET'])
@login_required
def get_companies_in_city():
    state = request.args.get('state', '')
    city = request.args.get('city', '')
    query = city + '~' + state
    company_objects = data_cache.hget(tragel_companies_tag, query)
    if company_objects:
        return send_response(200, json.loads(company_objects.decode('utf-8')))
    db_query = db.session.query(Company).join(City).join(State).filter(
        State.name==state, City.name==city).filter(
        State.id==City.state_id).filter(Company.city_id==City.id)
    companies = [company.to_json(with_isoformat=True) for company in
                 db_query.all()]
    data_cache.hset(tragel_companies_tag, query, json.dumps(companies))
    return send_response(200, companies)
