from flask import request, jsonify
from flask_login import login_user, logout_user, login_required

from ..auth import su_auth
from ..decorators import json
from ..login_blueprint import login_api
from ..models import User, Company
from ..utils import is_all_type, is_valid_string, find_occurrences, \
    https_url_for, send_error, log_activity


@login_api.route('/login', methods=['POST'])
def login_route():
    login_data = request.get_json()
    if login_data is None:
        return send_error(400, 'Bad request', 'Invalid data sent for login')
    full_username = login_data.get('username')
    password = login_data.get('password')
    company_token = login_data.get('token')
    login_credentials = [full_username, password, company_token]

    if not (is_all_type(login_credentials, str) or is_valid_string(login_credentials)):
        return send_error(400, 'Invalid credentials',
                          'You tried to login with invalid credentials')
    try:
        all_at_pos = find_occurrences('@', full_username)
        company_id = 0
        if len(all_at_pos) > 2:
            username = all_at_pos[0] + '@' + all_at_pos[1]
            company_id = int(all_at_pos[2])
        elif len(all_at_pos) == 2:
            username = all_at_pos[0]
            company_id = int(all_at_pos[1])
        else:
            username = full_username
        user = User.query.filter_by(username=username).first()
        if user is None or user.verify_password(password) is False or \
                user.company.verify_auth_token(company_token) != company_id:
            raise Exception('We could not verify the user\'s credentials')
        login_user(user)
        response = jsonify({'message': 'Logged in', 'status': 200 })
        response.status_code = 200
        return response
    except Exception as e:
        log_activity('LOGIN[login_route]', by_=full_username, for_=full_username,
                     why_=str(e))
        return send_error(400, 'Invalid credentials',
                          'You tried to login with a badly formed credential')


@login_api.route('/logout')
@login_required
@json
def logout_route():
    logout_user()
    return {}


@login_api.route('/endpoints', methods=['GET'])
@su_auth.login_required
def get_all_endpoints():
    company_id = request.args.get('company_id')
    company = Company.query.get(company_id)
    company_token = '' if company is None else company.generate_auth_token()
    response = jsonify({'login': https_url_for('login.login_route'),
                        'logout': https_url_for('login.logout_route'),
                        'create_user': https_url_for('api.create_user'),
                        'reset_password': https_url_for('api.reset_password'),
                        'delete_user': https_url_for('api.delete_user'),
                        'change_role': https_url_for('api.change_user_role'),
                        'get_subscriptions': https_url_for('api.get_subscriptions'),
                        'add_subscription': https_url_for('api.add_subscription'),
                        'get_products': https_url_for('api.get_products'),
                        'get_product': https_url_for('api.get_product', product_id=0),
                        'update_product': https_url_for('api.edit_product',
                                                        product_id=0),
                        'add_product': https_url_for('api.new_product'),
                        'get_orders': https_url_for('api.get_orders'),
                        'get_customer_order': https_url_for('api.get_customer_orders',
                                                            order_id=0),
                        'add_order': https_url_for('api.new_customer_order'),
                        'remove_order': https_url_for('api.delete_order', order_id=0),
                        'upload_images': https_url_for('api.upload_image_route'),
                        'ping': https_url_for('login.echo_ping'),
                        'company_id': company_id, 'company_token': company_token
                        })
    response.status_code = 200
    return response


@login_api.route('/ping', methods=['GET'])
@json
def echo_ping():
    return {'status': 'OK'}, 200, {}
