from flask import session as login_session, redirect
from app.models import *
from app.handlers import session
from functools import wraps


def authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not login_session.has_key('user_id'):
            return redirect('/login')
        else:
            try:
                user = session.query(User).filter_by(id=login_session.get('user_id')).one()
            except Exception:
                return redirect('/')
            kwargs['user'] = user
            return func(*args, **kwargs)

    return wrapper



