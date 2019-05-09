from flask import request, jsonify
from flask_login import login_user, logout_user, login_required
from ..models import User, db
from ..utils import is_all_type, is_valid_string, find_occurrences, https_url_for
from ..login_blueprint import login_api
from ..decorators import json


@login_api.route('/login', method=['POST'])
@json
def login_route():
    login_data = request.get_json()
    error_response = jsonify({'status': 400})
    error_response.status_code = 400

    if login_data is None:
        error_response['error'] = 'Bad request'
        error_response['message'] = 'Invalid data sent for login'
        return error_response
    full_username = login_data.get('username')
    password = login_data.get('password')
    company_token = login_data.get('token')
    login_credentials = [full_username, password, company_token]

    if not(is_all_type(login_credentials, str) or is_valid_string(login_credentials)):
        error_response['error'] = 'Invalid credentials'
        error_response['message'] = 'You tried to login with invalid credentials'
        return error_response
    try:
        all_at_pos = find_occurrences('@', full_username)
        if len(all_at_pos) > 2:
            username = all_at_pos[0] + '@' + all_at_pos[1]
            company_name = all_at_pos[2]
        elif len(all_at_pos) == 2:
            username = all_at_pos[0]
            company_name = all_at_pos[1]
        else:
            raise Exception
        user = db.session.query(User).filter_by(username=username).first()
        if user is None or user.verify_password(password) is False or \
                user.company.verify_auth_token(company_token) != company_name:
            raise Exception
        login_user(user)
        return {}, 200, {'Login': https_url_for('login_api.login_route')}
    except:
        error_response['error'] = 'Invalid credentials'
        error_response['message'] = 'You tried to login with badly formed credentials'
        return error_response


@login_api.route('/logout')
@login_required
@json
def logout_route():
    logout_user()
    return {}
