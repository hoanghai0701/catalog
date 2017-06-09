from flask import make_response
import json
from app.handlers import session

from app.models import *


class CustomError(RuntimeError):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code


def json_response(obj, status):
    response = make_response(json.dumps(obj), status)
    response.headers['Content-Type'] = 'application/json'
    return response


def get_user_by_email(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None




