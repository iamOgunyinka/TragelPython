from flask import request, jsonify
from flask_login import current_user
import base64
from . import v1_api, admin_required
from ..models import db, User
from ..decorators import json
from ..utils import is_all_type, BASIC_USER, SUPER_USER, find_occurrences, \
    https_url_for, send_password_reset, log_activity


@v1_api.route('/create_user', methods=['POST'])
@admin_required
@json
def create_user():
    json_data = request.get_json()
    error_response = jsonify({'status': 400, 'error': 'Bad request',
                              'message': 'This request contains invalid or no data'})
    error_response.status_code = 400
    if json_data is None:
        return error_response
    # base64 combination of username:password
    base64_username_password = json_data.get('username_password')
    fullname = json_data.get('name')
    personal_email = json_data.get('email')
    role = json_data.get('type', BASIC_USER)
    if is_all_type([base64_username_password, personal_email], str) or \
            type(role) != int or (BASIC_USER < role or role >= SUPER_USER):
        return error_response
    try:
        raw_data = base64.b64decode(base64_username_password)
        data_list = find_occurrences(':', raw_data)
        username = data_list[0] + '@' + current_user.company.name
        password = data_list[1]
    except Exception:
        return error_response
    user = User(username=username, password=password, personal_email=personal_email,
                role=role, company_id=current_user.company_id, fullname=fullname)
    db.session.add(user)
    db.session.commit()
    return {}, 201, {'Login': https_url_for('login_api.login_route')}


@v1_api.route('/reset_password', methods=['POST'])
@json
@admin_required
def reset_password():
    json_data = request.get_json()
    if json_data is None:
        error_response = jsonify({'status': 400, 'error': 'Bad request',
                                  'message': 'This request contains invalid or no data'})
        error_response.status_code = 400
        return error_response
    personal_email = json_data.get('email')
    username = json_data.get('username')
    user = db.session.query(User).filter_by(username=username,
                                            personal_email=personal_email).first()
    if user is None:
        error_response = jsonify({'error': 'Does not exist', 'status': 404,
                                  'message': 'The user with the information '
                                             'provided does not exist'})
        error_response.status_code_code = 404
        return error_response
    if user.company_id != current_user.company_id:
        error_response = jsonify({'error': 'Forbidden', 'status': 403})
        error_response['message'] = 'You\'re not allowed to reset this user\'s' \
                                    ' password'
        error_response.status_code = 403
        return error_response
    log_activity(event_type='PASSWORD RESET', by_=current_user.username,
                 for_=username, why_='')
    send_password_reset(user.id, user.company_id)
    return {}, 201, {'Login': https_url_for('login_api.login_route')}


@v1_api.route('/delete_user', methods=['DELETE'])
@admin_required
@json
def delete_user():
    reason = base64.b64decode(request.args.get('reason'))
    username = request.args.get('username')
    company_id = current_user.company_id
    log_activity(event_type='DELETE', by_=current_user.username, for_=username,
                 why_=reason)
    user = db.session.query(User).filter_by(username=username, company_id=company_id)
    if user is None:
        error_response = jsonify({'error': 'Does not exist', 'status': 404,
                                  'message': 'The user with the information '
                                             'provided does not exist'})
        error_response.status_code_code = 404
        return error_response
    db.session.delete(user)
    db.session.commit()
    return {}, 202, {'Message': 'Successful'}


@v1_api.route('/change_role/<int:user_id>', methods=['PUT'])
@admin_required
@json
def change_user_role(user_id):
    json_data = request.get_json()
    if json_data is None:
        error_response = jsonify({'status': 400, 'error': 'Bad request',
                                  'message': 'This request contains invalid or no data'})
        error_response.status_code = 400
        return error_response
    user = User.query.get_or_404(user_id)
    if not user or user.company_id != current_user.company_id:
        error_response = jsonify({'error': 'Does not exist', 'status': 404,
                                  'message': 'The user with the information '
                                             'provided does not exist'})
        error_response.status_code_code = 404
        return error_response
    try:
        user.role = int(json_data.get('role', BASIC_USER))
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        log_activity('SERVER ERROR', by_='', for_='', why_=str(e))
        error_response = jsonify({'error': 'Bad request received', 'status': 400,
                                  'message': 'The data is malformed'})
        error_response.status_code_code = 400
        return error_response
    return {}, 202, {'Message': 'Successful'}
