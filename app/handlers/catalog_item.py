from app import app
from app.utils.decorators import authenticated
from app.handlers import session
from flask import render_template, request, redirect, url_for, flash
from app.models import Catalog, Item


@app.route('/catalogs/<int:catalog_id>/items')
def item_index(catalog_id, *args, **kwargs):
    catalogs = session.query(Catalog).all()
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = catalog.items

    return render_template('catalog-item-index.html',
                           catalog=catalog,
                           items=items,
                           catalogs=catalogs)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>')
def item_show(catalog_id, item_id, *args, **kwargs):
    item = session.query(Item).filter_by(catalog_id=catalog_id, id=item_id).one()
    return render_template('catalog-item-show.html', item=item)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>/edit', methods=['GET'])
@authenticated
def item_edit(catalog_id, item_id, *args, **kwargs):
    item = session.query(Item).filter_by(catalog_id=catalog_id, id=item_id).one()
    user = kwargs['user']
    if item.user_id != user.id:
        return redirect(url_for('item_index', catalog_id=catalog_id))

    catalogs = session.query(Catalog).all()

    return render_template('catalog-item-edit.html', item=item, catalogs=catalogs)


@app.route('/items/<int:item_id>/edit', methods=['POST'])
@authenticated
def item_edit_confirm(item_id, **kwargs):
    item = session.query(Item).filter_by(id=item_id).one()
    user = kwargs['user']

    if item.user_id != user.id:
        return redirect(url_for('item_index', catalog_id=item.catalog_id))

    name = request.form.get('name', None)
    description = request.form.get('description', None)

    if not name or not description:
        flash('Both item name and description are required', 'error')
        return redirect(url_for('item_edit', catalog_id=item.catalog_id, item_id=item_id))

    catalog_id = request.form.get('catalog_id')

    item.name = name
    item.description = description
    item.catalog_id = catalog_id

    session.commit()

    return redirect(url_for('item_index', catalog_id=item.catalog_id))


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>/delete', methods=['GET'])
@authenticated
def item_delete(catalog_id, item_id, *args, **kwargs):
    user = kwargs['user']
    item = session.query(Item).filter_by(catalog_id=catalog_id, id=item_id).one()

    if user.id != item.user_id:
        return redirect(url_for('item_index', catalog_id=catalog_id))

    return render_template('catalog-item-delete.html', item=item)


@app.route('/catalogs/<int:catalog_id>items/<int:item_id>/delete', methods=['POST'])
@authenticated
def item_delete_confirm(catalog_id, item_id, **kwargs):
    user = kwargs['user']
    item = session.query(Item).filter_by(catalog_id=catalog_id, id=item_id).one()

    if user.id != item.user_id:
        return redirect(url_for('item_index', catalog_id=catalog_id))

    session.delete(item)
    session.commit()

    return redirect(url_for('item_index', catalog_id=catalog_id))


@app.route('/catalogs/<int:catalog_id>/items/create', methods=['GET'])
@authenticated
def item_create(catalog_id, **kwargs):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()

    return render_template('catalog-item-create.html', catalog=catalog)


@app.route('/catalogs/<int:catalog_id>/items', methods=['POST'])
@authenticated
def item_create_confirm(catalog_id, **kwargs):
    user = kwargs['user']
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()

    name = request.form.get('name', None)
    description = request.form.get('description', None)

    if not name or not description:
        flash('Both item name and description are required', 'error')
        return redirect(url_for('item_create', catalog_id=catalog_id))

    item = Item(name=name, description=description, catalog_id=catalog.id, user_id=user.id)
    session.add(item)
    session.commit()

    return redirect(url_for('item_index', catalog_id=catalog_id))
