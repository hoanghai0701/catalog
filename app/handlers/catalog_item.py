from app import app
from app.utils.decorators import authenticated, catalog_exists, item_exists, user_owns_item
from app.utils.helpers import json_response
from app.handlers import session
from flask import request, g
from app.models import Item


@app.route('/catalogs/<int:catalog_id>/items', methods=['GET'])
@catalog_exists
def item_list(catalog_id):
    catalog = g.catalog
    items = catalog.items

    return json_response(200, 'Get items list successfully', [item.serialize for item in items])


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>', methods=['GET'])
@item_exists
@catalog_exists
def item_show(catalog_id, item_id):
    item = g.item

    return json_response(200, 'Get item successfully', item.serialize)


@app.route('/catalogs/<int:catalog_id>/items', methods=['POST'])
@catalog_exists
@authenticated
def item_create(catalog_id):
    catalog = g.catalog
    user = g.user
    name = request.json.get('name', None)
    description = request.json.get('description', None)

    error = {}

    if not name:
        error['name'] = ['Item name is required']
    if not description:
        error['description'] = ['Item description is required']

    if error:
        return json_response(400, 'Missing arguments', error)

    item = Item(name=name, description=description, catalog_id=catalog.id, user_id=user.id)
    session.add(item)
    session.commit()
    session.refresh(item)

    return json_response(200, 'Create item successfully', item.serialize)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>', methods=['PUT'])
@item_exists
@catalog_exists
@authenticated
@user_owns_item
def item_update(catalog_id, item_id):
    item = g.item

    name = request.json.get('name', None)
    description = request.json.get('description', None)

    error = {}

    if not name:
        error['name'] = ['Item name is required']
    if not description:
        error['description'] = ['Item description is required']

    if error:
        return json_response(400, 'Missing arguments', error)

    item.name = name
    item.description = description
    session.commit()
    session.refresh(item)

    return json_response(200, 'Update item successfully', item.serialize)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>', methods=['DELETE'])
@item_exists
@catalog_exists
@authenticated
@user_owns_item
def item_delete(catalog_id, item_id):
    item = g.item
    session.delete(item)
    session.commit()

    return json_response(200, 'Delete item successfully')
