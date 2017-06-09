from flask import session as login_session, redirect, g
from app.models import User, Catalog, Item
from app.handlers import session
from functools import wraps
from app.utils.helpers import json_response


def authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not login_session.has_key('user_id'):
            return redirect('/login')
        else:

            user = session.query(User).filter_by(id=login_session.get('user_id')).first()
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


