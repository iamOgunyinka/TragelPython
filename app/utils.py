import logging
import os
import uuid
from datetime import date
from functools import partial

from flask import url_for as http_url_for, jsonify
from flask_uploads import UploadNotAllowed

log_cfg = os.path.join(os.getcwd(), 'logs', 'all_logs.txt')
logging.basicConfig(filename=log_cfg, filemode='a+',
                    format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
https_url_for = partial(http_url_for, _scheme='https', _external=True)


class SearchType:
    BY_PAYMENT_REF = 0
    BY_CASH_PAYMENT = 1
    BY_COMPANY_USER = 2
    BY_PUBLIC_USER = 3


class PaymentType:
    Cash = 0
    EBanking = 1


def generate_payment_id():
    return uuid.uuid4().hex


def date_from_string(text, default_date):
    if text is None:
        return default_date
    split_text_string = text.split('-')
    if len(split_text_string) < 3:
        return default_date
    (year, month, day) = (int(split_text_string[0]),
                          int(split_text_string[1]),
                          int(split_text_string[2]))
    try:
        new_date = date(year, month, day)
        return new_date
    except ValueError:
        return default_date


def is_valid_string(list_of_values):
    return filter(lambda value: value is not None and len(value) > 0,
                  list_of_values) != []


def is_all_type(list_of_values, value_type: type):
    for value in list_of_values:
        if type(value) != value_type:
            return False
    return True


def find_occurrences(substring: str, whole_string: str) -> list:
    return whole_string.split(substring)


def send_response(status_code, status, message=''):
    response = jsonify({'status': status, 'message': message})
    response.status_code = status_code
    return response


def log_activity(event_type, by_, for_, why_, **kwargs):
    logging.error(msg=[event_type, by_, for_, why_], **kwargs)


def upload(upload_object, request_object, company_id, data) -> dict:
    if data in request_object.files:
        try:
            filename = upload_object.save(request_object.files[data],
                                          folder=str(company_id))
            url = upload_object.url(filename)
            if not url.startswith('https'):
                url = url.replace('http', 'https', 1)
            return {'url': url}
        except UploadNotAllowed:
            return {'error': 'Upload type not allowed'}
    return {'error': 'Image contain invalid data'}
