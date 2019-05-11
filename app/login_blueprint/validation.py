from flask import request
from flask_login import login_user, logout_user, login_required
from ..models import User, db
from ..utils import is_all_type, is_valid_string, find_occurrences, \
    https_url_for, send_error, log_activity
from ..login_blueprint import login_api
from ..decorators import json


@login_api.route('/login', methods=['POST'])
def login_route():
    login_data = request.get_json()
    if login_data is None:
        return send_error(400, 'Bad request', 'Invalid data sent for login')
    full_username = login_data.get('username')
    password = login_data.get('password')
    company_token = login_data.get('token')
    login_credentials = [full_username, password, company_token]

    if not(is_all_type(login_credentials, str) or is_valid_string(login_credentials)):
        return send_error(400, 'Invalid credentials',
                          'You tried to login with invalid credentials')
    try:
        all_at_pos = find_occurrences('@', full_username)
        print(all_at_pos)
        if len(all_at_pos) > 2:
            username = all_at_pos[0] + '@' + all_at_pos[1]
            company_name = all_at_pos[2]
        elif len(all_at_pos) == 2:
            username = all_at_pos[0]
            company_name = all_at_pos[1]
        else:
            username = full_username
        user = db.session.query(User).filter_by(username=username).first()
        if user is None or user.verify_password(password) is False or \
                user.company.verify_auth_token(company_token) != company_name:
            print(user)
            raise Exception('We could not verify the password')
        login_user(user)
        return {}, 200, {'Login': https_url_for('login_api.login_route')}
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