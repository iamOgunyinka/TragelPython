import base64

from flask import request
from flask_login import current_user

from . import v1_api
from ..decorators import json
from ..models import db, User
from ..utils import is_all_type, BASIC_USER, SUPER_USER, find_occurrences, \
    https_url_for, send_password_reset, log_activity, send_error, admin_required


@v1_api.route('/create_user', methods=['POST'])
@admin_required
@json
def create_user():
    json_data = request.get_json()
    if json_data is None:
        return send_error(400, 'Bad request', 'This request contains invalid or no data')
    # base64 combination of username:password
    base64_username_password = json_data.get('username_password')
    fullname = json_data.get('name')
    personal_email = json_data.get('email')
    role = json_data.get('type', BASIC_USER)
    if is_all_type([base64_username_password, personal_email], str) or \
            type(role) != int or (BASIC_USER < role or role >= SUPER_USER):
        return send_error(400, 'Bad request', 'This request contains invalid or no data')
    try:
        raw_data = base64.b64decode(base64_username_password)
        data_list = find_occurrences(':', raw_data)
        username = data_list[0] + '@' + current_user.company.name
        password = data_list[1]
    except Exception as e:
        log_activity('EXCEPTION[create_user]', current_user.username, '', str(e))
        return send_error(400, 'Bad request', 'This request contains invalid or no data')
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
        return send_error(400, 'Bad request',
                          'This request contains invalid or no data')
    personal_email = json_data.get('email')
    username = json_data.get('username')
    user = db.session.query(User).filter_by(username=username,
                                            personal_email=personal_email).first()
    if user is None:
        return send_error(404, 'Does not exist',
                          'The user with the information provided does not exist')
    if user.company_id != current_user.company_id:
        return send_error(403, 'Forbidden',
                          'You\'re not allowed to reset this user\'s password')
    log_activity(event_type='PASSWORD RESET[reset_password]',
                 by_=current_user.username, for_=username, why_='')
    send_password_reset(user.id, user.company_id)
    return {}, 201, {'Login': https_url_for('login_api.login_route')}


@v1_api.route('/delete_user', methods=['DELETE'])
@admin_required
@json
def delete_user():
    reason = base64.b64decode(request.args.get('reason'))
    username = request.args.get('username')
    company_id = current_user.company_id
    log_activity(event_type='DELETE[delete_user]', by_=current_user.username,
                 for_=username, why_=reason)
    user = db.session.query(User).filter_by(username=username, company_id=company_id)
    if user is None:
        return send_error(404, 'Does not exist',
                          'The user with the information provided does not exist')
    db.session.delete(user)
    db.session.commit()
    return {}, 202, {'Message': 'Successful'}


# @v1_api.route('/change_role/<int:user_id>', methods=['PUT'])
@v1_api.route('/change_role', methods=['PUT'])
@admin_required
@json
def change_user_role():
    json_data = request.get_json()
    user_id = int(request.args.get('user_id'))
    if json_data is None:
        return send_error(400, 'Bad request', 'This request contains invalid or no data')
    user = User.query.get_or_404(user_id)
    if not user or user.company_id != current_user.company_id:
        return send_error(404, 'Does not exist',
                          'The user with the information provided does not exist')
    try:
        user.role = int(json_data.get('role', BASIC_USER))
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        log_activity('SERVER ERROR[change_user_role]', by_='', for_='', why_=str(e))
        return send_error(400, 'Bad request received', 'The data is malformed')
    return {}, 202, {'Message': 'Successful'}


