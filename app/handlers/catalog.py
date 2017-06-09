from app import app
from app.handlers import session
from app.utils.helpers import json_response
from app.utils.decorators import authenticated, catalog_exists, user_owns_catalog
from flask import request, g
from app.models import Catalog


@app.route('/catalogs', methods=['GET'])
def catalog_list():
    catalogs = session.query(Catalog).all()
    return json_response(200, 'Get catalogs list successfully', [catalog.serialize for catalog in catalogs])


@app.route('/catalogs/<int:catalog_id>', methods=['GET'])
@catalog_exists
def catalog_show(catalog_id):
    catalog = g.catalog
    return json_response(200, 'Get catalog successfully', catalog.serialize)


@app.route('/catalogs', methods=['POST'])
@authenticated
def catalog_create():
    name = request.json.get('name', None)
    if not name:
        return json_response(400, 'Missing arguments', {'name': ['Catalog name is required']})

    user = g.user
    catalog = Catalog(name=name, user_id=user.id)
    session.add(catalog)
    session.commit()
    session.refresh(catalog)

    return json_response(200, 'Create catalog successfully', catalog.serialize)


@app.route('/catalogs/<int:catalog_id>', methods=['PUT'])
@authenticated
@catalog_exists
@user_owns_catalog
def catalog_update(catalog_id):
    catalog = g.catalog

    name = request.json.get('name', None)

    if not name:
        return json_response(400, 'Missing arguments', {'name': ['Catalog name is required']})

    catalog.name = name
    session.commit()
    session.refresh(catalog)

    return json_response(200, 'Update catalog successfully', catalog.serialize)


@app.route('/catalogs/<int:catalog_id>', methods=['DELETE'])
@authenticated
@catalog_exists
@user_owns_catalog
def catalog_delete(catalog_id):
    catalog = g.catalog

    session.delete(catalog)
    session.commit()

    return json_response(200, 'Delete catalog successfully')








