from flask import request, g
from app.models import User, Catalog, Item
from app.handlers import session
from functools import wraps
from app.utils.helpers import json_response
import jwt
import re
from app import app


def authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('AUTHORIZATION', None)
        if not auth:
            return json_response(403, 'Token not found')

        auth = re.sub("\s+", " ", auth.rstrip().lstrip()).split(' ')

        if len(auth) != 2:
            return json_response(403, 'Invalid header')

        scheme, token = auth
        if scheme != app.config.get('JWT_SCHEME'):
            return json_response(403, 'Invalid header')

        try:
            payload = jwt.decode(token, app.secret_key)
            user_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return json_response(403, 'Expired token')
        except jwt.InvalidTokenError:
            return json_response(403, 'Invalid token')

        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return json_response(404, 'User not found')
        g.user = user
        return func(*args, **kwargs)

    return wrapper


def catalog_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        catalog_id = kwargs['catalog_id']
        catalog = session.query(Catalog).filter_by(id=catalog_id).first()

        if not catalog:
            return json_response(404, 'Catalog not found')

        g.catalog = catalog

        return func(*args, **kwargs)

    return wrapper


def item_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        catalog_id = kwargs['catalog_id']
        item_id = kwargs['item_id']
        item = session.query(Item).filter_by(id=item_id, catalog_id=catalog_id).first()

        if not item:
            return json_response(404, 'Item not found')

        g.item = item

        return func(*args, **kwargs)

    return wrapper


def user_owns_catalog(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = g.user
        catalog = g.catalog

        if catalog.user_id != user.id:
            return json_response(403, 'You are not permitted to access this catalog')

        return func(*args, **kwargs)

    return wrapper


def user_owns_item(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = g.user
        item = g.item

        if item.user_id != user.id:
            return json_response(403, 'You are not permitted to access this item')

        return func(*args, **kwargs)

    return wrapper
