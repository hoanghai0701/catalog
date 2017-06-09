import json
from app.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import g
from werkzeug.local import LocalProxy
from app import app

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

APP_ID = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
APP_SECRET = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']


def get_session():
    session = getattr(g, '_session', None)

    if not session:
        engine = create_engine('sqlite:///catalog.db')
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        g._session = session = DBSession()

    return session

session = LocalProxy(get_session)


@app.teardown_appcontext
def teardown_session(exception):
    session = getattr(g, '_session', None)
    if session is not None:
        session.close()


