import json

from flask import current_app
from flask import json

JSON_TYPE = (dict, list)

UTF8 = "utf8"

APP_JSON = 'application/json'


def ok(body, status_code=200):
    return response(body, status_code)


def bad_request(body, status_code=400):
    return response(body, status_code)


def server_error(body, status_code=500):
    return response(body, status_code)


def not_found(body, status_code=404):
    return response(body, status_code)


def response(body, status_code):
    validate_message(body)

    json_message = json.dumps(body, indent=2, separators=(', ', ':'), encoding=UTF8)

    return current_app.response_class(response=json_message, status=status_code,
                                      mimetype=APP_JSON,
                                      content_type='{type}; charset={charset}'.format(type=APP_JSON,charset=UTF8))


def validate_message(body):
    if not isinstance(body, JSON_TYPE):
        raise TypeError("response body must be dict or array")