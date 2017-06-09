from app import app
from app.handlers import session
from app.utils.helpers import json_response
from app.utils.decorators import authenticated
from flask import render_template, request, redirect, flash, url_for
from app.models import Catalog, Item


@app.route('/', methods=['GET'])
def index():
    catalogs = session.query(Catalog).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(10).all()
    return render_template('base.html', catalogs=catalogs, items=items)


@app.route('/catalogs/create', methods=['GET'])
@authenticated
def create(*args, **kwargs):
    return render_template('catalog-create.html')


@app.route('/catalogs', methods=['POST'])
@authenticated
def store(*args, **kwargs):
    name = request.form.get('name', None)
    if not name:
        flash('Catalog name is required', 'error')
        return redirect(url_for('create'))

    user = kwargs['user']
    catalog = Catalog(name=name, user_id=user.id)
    session.add(catalog)
    session.commit()

    return redirect('/')


@app.route('/catalogs/json', methods=['GET'])
def json(*args, **kwargs):
    catalogs = session.query(Catalog).all()
    json = {'catalogs': [catalog.serialize for catalog in catalogs]}
    return json_response(json, 200)


