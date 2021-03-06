import base64

from flask import request, jsonify
from flask_login import current_user

from . import v1_api
from ..decorators import paginate, UserType, permission_required, \
    fully_subscribed
from ..models import db, User
from ..utils import is_all_type, find_occurrences, log_activity, send_response


@v1_api.route('/create_user', methods=['POST'])
@permission_required(UserType.Administrator)
@fully_subscribed
def create_user():
    json_data = request.get_json()
    if json_data is None:
        return send_response(401, 'This request contains no user data')
    # base64 combination of username:password
    base64_username_password = json_data.get('username_password')
    fullname = json_data.get('name')
    personal_email = json_data.get('email')
    personal_address = json_data.get('address')
    role = json_data.get('type', UserType.BasicUser)
    if is_all_type([base64_username_password, personal_email], str) is False or \
            type(role) != int or (role < UserType.BasicUser or
                                  role >= UserType.SuperUser):
        return send_response(402,
                             'This request\'s data is in an unrecognized format')
    try:
        raw_data = base64.b64decode(base64_username_password).decode()
        data_list = find_occurrences(':', raw_data)
        username = data_list[0] + '@' + str(current_user.company_id)
        password = data_list[1]
    except Exception as e:
        log_activity('EXCEPTION[create_user]', current_user.username, '',
                     str(e))
        return send_response(400, 'This request contains invalid or no data')

    user = User(username=username, password=password,
                personal_email=personal_email,
                role=role, company_id=current_user.company_id,
                fullname=fullname)
    if personal_address is not None and len(personal_address) > 0:
        user.address = personal_address
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_activity('EXCEPTION[create_user]', current_user.username, '',
                     str(e))
        return send_response(403, 'Unable to add the user to our network')
    return send_response(200, 'OK')


@v1_api.route('/reset_password', methods=['POST'])
@permission_required(UserType.Administrator)
@fully_subscribed
def reset_password():
    json_data = request.get_json()
    if json_data is None:
        return send_response(400, 'This request contains invalid or no data')
    new_password = json_data.get('new_password', '')
    email = json_data.get('email', '')
    if len(new_password)<8:
        return send_response(400, 'Password too short')
    user = db.session.query(User).filter_by(personal_email=email,
                                            company_id=current_user.company_id).first()
    if user is None:
        return send_response(404, 'The user with the information provided does '
                                  'not exist')
    if user == current_user:
        return send_response(403,
                             'You\'re not allowed to reset your own password\'s '
                             'while logged in')
    log_activity(event_type='PASSWORD RESET[reset_password]',
                 by_=current_user.username, for_=email, why_='')
    user.password = new_password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        log_activity('PASSWORD RESET[Exception]', current_user.username,
                     user.username, str(e))
        return send_response(403, 'Forbidden', 'Invalid operation')
    return send_response(200, 'Change successful')


@v1_api.route('/delete_user', methods=['DELETE'])
@permission_required(UserType.Administrator)
@fully_subscribed
def delete_user():
    payload = base64.b64decode(request.args.get('payload')).decode()
    payload = payload.split(':') if payload else ':'
    if len(payload) < 3:
        return send_response(401, 'Needs additional information')
    email = payload[0]
    admin_password = payload[1]
    reason = payload[2]
    company_id = current_user.company_id

    if not current_user.verify_password(admin_password):
        return send_response(401, 'Password is incorrect')
    user = User.query.filter_by(personal_email=email, company_id=company_id).first()
    if user is None or user == current_user:
        return send_response(404, 'The user with the information provided does '
                                  'not exist')
    user.deleted = True
    db.session.commit()
    log_activity(event_type='DELETE[delete_user]', by_=current_user.username,
                 for_=email, why_=reason)
    response = jsonify({'status': 'Successful', 'status_code': 200})
    response.status_code = 200
    return response


@v1_api.route('/change_role/', methods=['GET'])
@permission_required(UserType.Administrator)
@fully_subscribed
def change_user_role():
    user_data = base64.b64decode(request.args.get('payload')).decode()
    user_id, role = user_data.split(':')
    user = User.query.get(int(user_id))
    if not user or user.company_id != current_user.company_id:
        return send_response(404, 'The user with the information provided does '
                                  'not exist')
    try:
        user.role = int(role) if role is not None else UserType.BasicUser
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        log_activity('SERVER ERROR[change_user_role]', by_='', for_='',
                     why_=str(e))
        return send_response(400, 'The data is malformed')
    return send_response(200, {'role': user.role})


@v1_api.route('/list_users', methods=['GET'])
@permission_required(UserType.Administrator)
@paginate("users")
@fully_subscribed
def list_users():
    return User.query.filter(User.company_id == current_user.company_id)
