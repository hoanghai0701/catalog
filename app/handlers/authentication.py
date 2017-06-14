from flask import request, g, session as login_session
from app.utils.helpers import json_response, get_user_by_email, CustomError
from app.utils.decorators import authenticated
from app import app
from app.models import User
from app.handlers import CLIENT_ID, APP_ID, APP_SECRET, session
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import requests
import json
import random
import string
import datetime
import jwt

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
        raise CustomError('Failed to upgrade the authorization code', 401)

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


def _create_user(username, email, picture):
    user = User(name=username,
                email=email,
                picture=picture)
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


def _generate_jwt(user):
    try:
        exp_duration = app.config.get('JWT_EXP')
        payload = {
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=exp_duration),
            'sub': user.id
        }
        return jwt.encode(payload, app.secret_key, algorithm='HS256')
    except Exception as e:
        raise e


@app.route('/logout', methods=['POST'])
@authenticated
def logout():
    if login_session.get('provider', None):
        if login_session['provider'] == providers['GOOGLE']:
            _revoke_google_token()
        elif login_session['provider'] == providers['FACEBOOK']:
            _revoke_facebook_token()

    return json_response(200, 'Logout successfully')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    code = request.json.get('access_token', None)

    if not code:
        return json_response(400, 'Access token is required')

    try:
        credentials, gplus_id = _exchange_google_access_token(code)
    except CustomError, e:
        return json_response(e.code, e.msg)

    # Get user info
    data = _get_google_user_info(credentials.access_token)
    user = get_user_by_email(data['email'])

    if not user:
        user = _create_user(data['name'], data['email'], data['picture'])

    try:
        jwt_token = _generate_jwt(user)
    except Exception:
        return json_response(500, 'Cannot create token')

    return json_response(200, 'Login with Google successfully', {'user': user.serialize, 'token': jwt_token})


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    token = request.json.get('access_token', None)

    if not token:
        return json_response(400, 'Access token is required')

    try:
        data, access_token = _get_facebook_user_data(token)
    except Exception, e:
        return json_response(500, 'Cannot get Facebook user info', e.message)

    user = get_user_by_email(data['email'])

    if not user:
        user = _create_user(data['name'], data['email'], data['picture'])

    try:
        jwt_token = _generate_jwt(user)
    except Exception:
        return json_response(500, 'Cannot create token')

    return json_response(200, 'Login with Facebook successfully', {'user': user.serialize, 'token': jwt_token})


@app.route('/profile', methods=['GET'])
@authenticated
def get_profile():
    return json_response(200, 'Get profile successfully', g.user.serialize)
