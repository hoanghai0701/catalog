import random
import string
from flask import make_response
from flask import session as login_session
import json
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from app.handlers import CLIENT_ID, APP_ID, APP_SECRET, session
import requests
from app.models import *


class CustomError(RuntimeError):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code


def random_string(n=32):
    s = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(n))
    return s


def json_response(obj, status):
    response = make_response(json.dumps(obj), status)
    response.headers['Content-Type'] = 'application/json'
    return response


def exchange_google_access_token(code):
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return json_response('Failed to upgrade the authorization code', 401)

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        raise CustomError(result.get('error'), 500)

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        raise CustomError("Token's user ID doesn't match given user ID", 401)

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        raise CustomError("Token's client ID does not match app's", 401)

    return credentials, gplus_id


def get_google_user_info(access_token):
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    return answer.json()


def get_facebook_user_data(token):
    print APP_ID, APP_SECRET
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' \
          % (APP_ID, APP_SECRET, token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # strip expire tag from access token
    access_token = json.loads(result)["access_token"]

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    picture_url = json.loads(result)['data']['url']

    data['picture'] = picture_url

    return data, access_token


def get_user_by_email(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None


def create_user(login_session):
    user = User(name=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def revoke_google_token():
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    return result


def revoke_facebook_token():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return result


def clear_login_session():
    login_session.pop('access_token', None)
    login_session.pop('username', None)
    login_session.pop('email', None)
    login_session.pop('picture', None)
    login_session.pop('user_id', None)
    login_session.pop('provider', None)



