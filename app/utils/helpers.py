from flask import jsonify
from app.handlers import session

from app.models import *


class CustomError(RuntimeError):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code


def json_response(status, msg, data=None):
    response = jsonify(msg=msg, data=data)
    response.status_code = status
    return response


def get_user_by_email(email):
    user = session.query(User).filter_by(email=email).first()
    return user
