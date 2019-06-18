import base64

from flask import request, jsonify
from flask_login import current_user

from . import v1_api
from ..decorators import json, paginate
from ..models import db, User
from ..utils import is_all_type, BASIC_USER, SUPER_USER, find_occurrences, \
    https_url_for, log_activity, send_error, admin_required


@v1_api.route('/create_user', methods=['POST'])
@admin_required
@json
def create_user():
    json_data = request.get_json()
    if json_data is None:
        return send_error(401, 'This request contains no userdata', 'Bad request')
    # base64 combination of username:password
    base64_username_password = json_data.get('username_password')
    fullname = json_data.get('name')
    personal_email = json_data.get('email')
    personal_address = json_data.get('address')
    role = json_data.get('type', BASIC_USER)
    if is_all_type([base64_username_password, personal_email], str) is False or\
            type(role) != int or (role < BASIC_USER or role >= SUPER_USER):
        return send_error(402, 'This request\'s data is in an unrecognized format',
                          'Bad request')
    try:
        raw_data = base64.b64decode(base64_username_password).decode()
        data_list = find_occurrences(':', raw_data)
        username = data_list[0] + '@' + str(current_user.company_id)
        password = data_list[1]
    except Exception as e:
        log_activity('EXCEPTION[create_user]', current_user.username, '', str(e))
        return send_error(400, 'Bad request',
                          'This request contains invalid or no data')

    user = User(username=username, password=password, personal_email=personal_email,
                role=role, company_id=current_user.company_id, fullname=fullname)
    if personal_address is not None and len(personal_address) > 0:
        user.address = personal_address
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[create_user]', current_user.username, '', str(e))
        return send_error(403, 'Error', 'Unable to add the user to our network')
    return jsonify({'message': 'OK'})


@v1_api.route('/reset_password', methods=['POST'])
@admin_required
@json
def reset_password():
    json_data = request.get_json()
    if json_data is None:
        return send_error(400, 'Bad request', 'This request contains invalid '
                                              'or no data')
    old_password = json_data.get('old_password')
    new_password = json_data.get('new_password')
    username = json_data.get('username')
    user = db.session.query(User).filter_by(username=username).first()
    if user is None or user.verify_password(old_password) is False:
        return send_error(404, 'Does not exist',
                          'The user with the information provided does not exist')
    if user.company_id != current_user.company_id:
        return send_error(403, 'Forbidden',
                          'You\'re not allowed to reset this user\'s password')
    log_activity(event_type='PASSWORD RESET[reset_password]',
                 by_=current_user.username, for_=username, why_='')
    user.password = new_password
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        log_activity('PASSWORD RESET[Exception]', current_user.username,
                     user.username, str(e))
        return send_error(403, 'Forbidden', 'Invalid operation')
    return {'Login': https_url_for('login_api.login_route')}, 201, {}


@v1_api.route('/delete_user', methods=['DELETE'])
@admin_required
@json
def delete_user():
    reason = base64.b64decode(request.args.get('reason'))
    username = request.args.get('username')
    admin_password = request.args.get('password')
    company_id = current_user.company_id

    if not current_user.verify_password(admin_password):
        return send_error(400, 'Invalid credential', 'Password is incorrect')
    user = db.session.query(User).filter_by(username=username, company_id=company_id)
    if user is None:
        return send_error(404, 'Does not exist',
                          'The user with the information provided does not exist')
    db.session.delete(user)
    db.session.commit()
    log_activity(event_type='DELETE[delete_user]', by_=current_user.username,
                 for_=username, why_=reason)
    return {'message': 'Successful'}, 202, {}


@v1_api.route('/change_role/<int:user_id>', methods=['PUT'])
@admin_required
@json
def change_user_role(user_id):
    json_data = request.get_json()
    if json_data is None:
        return send_error(400, 'Bad request',
                          'This request contains invalid or no data')
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


@v1_api.route('/list_users', methods=['GET'])
@admin_required
@json
@paginate("users", 100)
def list_users():
    if current_user.role != SUPER_USER:
        return User.query.filter_by(company_id=current_user.company_id)
    return User.query.filter_by(company_id=current_user.company_id, role=BASIC_USER)
