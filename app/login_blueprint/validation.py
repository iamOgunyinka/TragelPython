from flask import request, jsonify
from flask_login import login_user, logout_user, login_required

from ..auth import su_auth
from ..login_blueprint import login_api
from ..models import User, Company
from ..utils import is_all_type, is_valid_string, https_url_for, \
    send_response, log_activity


@login_api.route('/login', methods=['POST'])
def login_route():
    login_data = request.get_json()
    if login_data is None:
        return send_response(400, 'Invalid data sent for login')
    username = login_data.get('username')
    password = login_data.get('password')
    company_token = login_data.get('token')
    login_credentials = [username, password, company_token]

    if not (is_all_type(login_credentials, str) or is_valid_string(login_credentials)):
        return send_response(401, 'You tried to login with invalid credentials')
    try:
        user = User.query.filter_by(username=username).first()
        if user is None or user.verify_password(password) is False:
            raise Exception('We could not verify the user\'s credentials')
        login_user(user)
    except Exception as e:
        log_activity('LOGIN[login_route]', by_=username, for_=username, why_=str(e))
        return send_response(402, 'You tried to login with a badly formed credential')
    return send_response(200, 'Logged in')


@login_api.route('/logout')
@login_required
def logout_route():
    logout_user()
    return send_response(204, '')


@login_api.route('/endpoints', methods=['GET'])
@su_auth.login_required
def get_all_endpoints():
    company_id = request.args.get('company_id', 0, type=int)
    company = Company.query.get(company_id)
    company_token = '' if company is None else company.generate_auth_token()
    response = jsonify({'login': https_url_for('login.login_route'),
                        'logout': https_url_for('login.logout_route'),
                        'create_user': https_url_for('api.create_user'),
                        'reset_password': https_url_for('api.reset_password'),
                        'delete_user': https_url_for('api.delete_user'),
                        'list_users': https_url_for('api.list_users'),
                        'change_role': https_url_for('api.change_user_role', user_id=0),
                        'get_subscriptions': https_url_for('api.get_subscriptions'),
                        'get_expiry': https_url_for('api.get_expiration'),
                        'add_subscription': https_url_for('api.add_subscription'),
                        'get_products': https_url_for('api.get_products'),
                        'get_product': https_url_for('api.get_product', product_id=0),
                        'remove_product': https_url_for('api.delete_product'),
                        'add_product': https_url_for('api.new_product'),
                        'get_orders': https_url_for('api.get_orders'),
                        'count_orders': https_url_for('api.order_count'),
                        'confirm_order': https_url_for('api.confirm_customer_order'),
                        'get_customer_order': https_url_for('api.get_customer_orders',
                                                            order_id=0),
                        'add_order': https_url_for('api.new_customer_order'),
                        'remove_order': https_url_for('api.delete_order'),
                        'upload_images': https_url_for('api.upload_image_route'),
                        'ping': https_url_for('login.echo_ping'),
                        'company_id': company_id, 'company_token': company_token
                        })
    response.status_code = 200
    return response


@login_api.route('/ping', methods=['GET'])
def echo_ping():
    return send_response(200, 'OK')
