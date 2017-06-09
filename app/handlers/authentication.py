from flask import render_template, request, redirect
from flask import session as login_session
from app.utils.helpers import json_response, get_user_by_email
from app.utils.helpers import CustomError
from app import app
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from app.handlers import CLIENT_ID, APP_ID, APP_SECRET, session
import requests
import json
from app.models import User
import random
import string

providers = {
    'GOOGLE': 'google',
    'FACEBOOK': 'facebook'
}


def _random_string(n=32):
    s = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(n))
    return s


def _exchange_google_access_token(code):
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


def _get_google_user_info(access_token):
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    return answer.json()


def _get_facebook_user_data(token):
    print APP_ID, APP_SECRET
    url = 'https://graph.facebook.com/oauth/access_token' \
          '?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' \
          % (APP_ID, APP_SECRET, token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # strip expire tag from access token
    access_token = json.loads(result)["access_token"]

    url = 'https://graph.facebook.com/v2.8/me' \
          '?access_token=%s&fields=name,id,email' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    url = 'https://graph.facebook.com/v2.8/me/picture' \
          '?access_token=%s&redirect=0&height=200&width=200' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    picture_url = json.loads(result)['data']['url']

    data['picture'] = picture_url

    return data, access_token


def _create_user(login_session):
    user = User(name=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _revoke_google_token():
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    return result


def _revoke_facebook_token():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return result


def _clear_login_session():
    login_session.pop('access_token', None)
    login_session.pop('username', None)
    login_session.pop('email', None)
    login_session.pop('picture', None)
    login_session.pop('user_id', None)
    login_session.pop('provider', None)


@app.route('/login', methods=['GET'])
def login():
    state = _random_string()
    login_session['state'] = state
    return render_template('login.html', state=state)


@app.route('/logout', methods=['GET'])
def logout():
    if login_session.has_key('provider'):
        if login_session['provider'] == providers['GOOGLE']:
            _revoke_google_token()
        elif login_session['provider'] == providers['FACEBOOK']:
            _revoke_facebook_token()

    _clear_login_session()
    return redirect('/')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        return json_response('Invalid state parameter', 401)

    # Obtain authorization code
    code = request.data

    try:
        credentials, gplus_id = _exchange_google_access_token(code)
    except CustomError, e:
        return json_response(e.msg, e.code)

    _clear_login_session()

    # Store the access token in the session for later use.
    login_session['provider'] = providers['GOOGLE']
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    data = _get_google_user_info(credentials.access_token)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user = get_user_by_email(login_session['email'])

    if not user:
        user = _create_user(login_session)

    login_session['user_id'] = user.id

    return json_response('Login successfully', 200)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        return json_response('Invalid state parameter', 401)

    token = request.data
    try:
        data, access_token = _get_facebook_user_data(token)
    except Exception, e:
        return json_response(e.message, 500)

    _clear_login_session()

    login_session['provider'] = providers['FACEBOOK']
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    login_session['access_token'] = access_token
    login_session['picture'] = data["picture"]

    user = get_user_by_email(login_session['email'])

    if not user:
        user = _create_user(login_session)

    login_session['user_id'] = user.id

    return json_response('Login successfully', 200)
