from flask import render_template, request, redirect, jsonify, url_for, flash, make_response
from app.utils.helpers import *
from app import app

providers = {
    'GOOGLE': 'google',
    'FACEBOOK': 'facebook'
}


@app.route('/login', methods=['GET'])
def login():
    state = random_string()
    login_session['state'] = state
    return render_template('login.html', state=state)


@app.route('/logout', methods=['GET'])
def logout():
    if login_session.has_key('provider'):
        if login_session['provider'] == providers['GOOGLE']:
            revoke_google_token()
        elif login_session['provider'] == providers['FACEBOOK']:
            revoke_facebook_token()

    clear_login_session()
    return redirect('/')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        return json_response('Invalid state parameter', 401)

    # Obtain authorization code
    code = request.data

    try:
        credentials, gplus_id = exchange_google_access_token(code)
    except CustomError, e:
        return json_response(e.msg, e.code)

    clear_login_session()

    # Store the access token in the session for later use.
    login_session['provider'] = providers['GOOGLE']
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    data = get_google_user_info(credentials.access_token)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user = get_user_by_email(login_session['email'])

    if not user:
        user = create_user(login_session)

    login_session['user_id'] = user.id

    return json_response('Login successfully', 200)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        return json_response('Invalid state parameter', 401)

    token = request.data
    try:
        data, access_token = get_facebook_user_data(token)
    except Exception, e:
        return json_response(e.message, 500)

    clear_login_session()

    login_session['provider'] = providers['FACEBOOK']
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    login_session['access_token'] = access_token
    login_session['picture'] = data["picture"]

    user = get_user_by_email(login_session['email'])

    if not user:
        user = create_user(login_session)

    login_session['user_id'] = user.id

    return json_response('Login successfully', 200)
