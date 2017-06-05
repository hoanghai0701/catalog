import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

APP_ID = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
APP_SECRET = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

from authentication import *
import catalog
from catalog_item import *
