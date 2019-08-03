import json

from flask import request

from . import mobile_auth, mobile_api
from ..models import State, City, Company, Product, User, db
from ..utils import data_cache, tragel_companies_tag, send_response, \
    log_activity
from ..auth import UserType


@mobile_api.route('/get_companies', methods=['GET'])
@mobile_auth.login_required
def get_companies_in_city():
    state = request.args.get('state', '')
    city = request.args.get('city', '')
    query = city + '~' + state
    company_objects = data_cache.hget(tragel_companies_tag, query)
    if company_objects:
        return send_response(200, json.loads(company_objects.decode('utf-8')))
    db_query = db.session.query(Company).join(City).join(State).filter(
        State.name == state, City.name == city).filter(
        State.id == City.state_id).filter(Company.city_id == City.id)
    companies = [company.to_json(with_isoformat=True) for company in
                 db_query.all()]
    data_cache.hset(tragel_companies_tag, query, json.dumps(companies))
    return send_response(200, companies)


@mobile_api.route('/get_products/<int:company_id>', methods=['GET'])
@mobile_auth.login_required
def get_company_products(company_id):
    products = [product.to_json() for product in Product.query.filter_by(
        company_id=company_id).order_by(Product.name).all()]
    return send_response(200, products)


@mobile_api.route('/login', methods=['POST'])
def confirm_login():
    login_data = request.get_json()
    if login_data is None:
        return send_response(400, 'Invalid data sent for login')
    username = login_data.get('username', '')
    password = login_data.get('password', '')

    try:
        user = User.query.filter_by(username=username).first()
        if user is None or user.verify_password(password) is False:
            raise Exception('We could not verify the user\'s credentials')
    except Exception as e:
        log_activity('LOGIN[login_route]', by_=username, for_=username,
                     why_=str(e))
        return send_response(402, 'You tried to login with a bad credential')
    return send_response(200, 'OK')


@mobile_api.route('/sign_up', methods=['POST'])
def sign_up_user():
    json_data = request.get_json()
    if json_data is None:
        return send_response(401, 'This request contains no user data')
    fullname = json_data.get('fullname')
    personal_address = json_data.get('address')
    personal_email = json_data.get('email')
    username = json_data.get('username')
    password = json_data.get('password')
    role = UserType.BasicUser
    if User.query.filter_by(username=username).first():
        return send_response(401, 'Username already registered')
    if User.query.filter_by(personal_email=personal_email).first():
        return send_response(401, 'Email already registered')
    user = User(username=username, password=password, personal_email=personal_email,
                role=role, company_id=1, fullname=fullname, address=personal_address)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[create_user]', username, '', str(e))
        return send_response(403, 'Unable to add the user to our network')
    return send_response(200, 'OK')
