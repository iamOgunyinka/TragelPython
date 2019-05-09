from functools import partial
from flask import url_for as http_url_for
from .decorators import permission_required

(SUPER_USER, ADMINISTRATOR, BASIC_USER) = (0x4C, 0x4B, 0x4A)
https_url_for = partial(http_url_for, _scheme='https', _external=True)


def admin_required(function):
    return permission_required(ADMINISTRATOR)(function)

def is_valid_string(list_of_values):
    return filter(lambda value: value is not None and len(value) > 0,
                  list_of_values) != []


def is_all_type(list_of_values, value_type: type):
    for value in list_of_values:
        if type(value) != value_type:
            return False
    return True


def find_occurrences(substring: str, whole_string: str) -> list:
    start = 0
    found = []
    index = whole_string.find(substring, start)
    while index != -1:
        store = whole_string[start:index]
        if len(store) > 0:
            found.append(store)
        start = index + 1
        index = whole_string.find(substring, start)
    return found


async def log_activity(event_type, by_, for_, why_, **kwargs):
    pass


def send_password_reset(user_id, company_id):
    pass