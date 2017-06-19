"""This module includes routes and functions for authentication and authorization."""

import httplib2
import requests
import json

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session as login_session
from flask import url_for

from catalog import app
from catalog.users import get_user_id, get_user_info, create_user

auth = Blueprint('auth', __name__)


################################################################################
# Aurthorization (login/logout)
################################################################################

@auth.route("/login/")
def login():
    """Show login page.

    Request arguments:
        next:
            The url to redirect to after login.
            If not specified, redirect to the catalog home page.
    """
    if "next" in request.args:
        next = request.args["next"]
    else:
        next = url_for("api.view_catalog")
    return render_template("auth/login.html", next = next)

@auth.route("/logout/")
def logout():
    # for now, just disconnect from google
    return redirect(url_for("auth.google_disconnect"))


################################################################################
# Authentication (permissions)
################################################################################

from functools import wraps

# TODO(pt314): consider using Flask-Login
# https://flask-login.readthedocs.org/en/latest/
def login_required(func):
    """Decorates a view to ensure that only logged in users can access it.

    Redirects user to login page if the user is not logged in.
    """
    @wraps(func)
    def login_required_route(*args, **kargs):
        if 'username' not in login_session:
            flash(message = "You are not authorized to access this page. Please login.", category = "info")
            return redirect(url_for('auth.login', next = request.url)) # save url to redirect after login
        return func(*args, **kargs)
    return login_required_route


################################################################################
# GOOGLE sign-in
################################################################################

from flask import request
from flask import make_response

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import OAuth2Credentials

import os
from catalog import app_root

@auth.route("/google_connect", methods = ["POST"])
def google_connect():
    """Sign in user with Google account."""

    # Obtain authorization code
    code = request.data

    # Upgrade the authorization code into a credentials object.
    try:
        oauth_flow = flow_from_clientsecrets(os.path.join(app_root, 'client_secret_google.json'), scope = '')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid. If there is an error in the token, abort.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(
            json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID does not match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['audience'] != app.config['GOOGLE_CLIENT_ID']:
        response = make_response(
            json.dumps("Token's client ID does not match app's client ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if user is already connected.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Everything OK. Now load user info and add store it in the session...

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    user_info = requests.get(userinfo_url, params = params)
    data = user_info.json()

    # Store user info in session.
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    email = login_session['email']
    user_id = get_user_id(email)
    if not user_id:
        user_id = create_user(login_session)
        login_session['user_id'] = user_id
    else:
        login_session['user_id'] = user_id

    flash(message = "You are now logged in as %s" % login_session['username'], category = "success")

    output = '<h1>Welcome, ' + login_session['username'] + '!</h1>'
    output += '<p>' + login_session['email'] + '</p>'
    output += '<img src="' + login_session['picture'] + '" class="img-circle" width="200">'
    return output


@auth.route('/google_disconnect')
def google_disconnect():
    """Sign out user with Google account."""

    # Only disconnect a connected user.
    access_token = login_session.get('credentials')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        # No need to do anything. User is still logged out.
        print "Failed to revoke access token. It may have been experired or invalid for another reason. User logged out."

    # Reset the user's session.
    login_session.clear()

    flash(message = "You are now logged out.", category = "success")
    return redirect(url_for('api.view_catalog'))

################################################################################
