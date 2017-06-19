import os
import json

from flask import Flask
from flask import render_template
# from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog.models import Base


app = Flask(__name__)

# App root folder
app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load client ids from config files
client_secret = os.path.join(app_root, 'client_secret_google.json')
app.config['GOOGLE_CLIENT_ID'] = json.loads(open(client_secret, 'r').read())['web']['client_id']


# Configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///catalog'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super_secret_key'
app.config['CSRF_SECRET_KEY'] = 'csfr_super_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(app_root, 'uploads')
app.config['ALLOWED_IMAGE_EXTENSIONS'] = set(['jpg', 'jpeg', 'png', 'gif'])


# Connect to database and create database session
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
db = DBSession()
# db = SQLAlchemy(app)


# Register HTTP error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    return render_template('500.html'), 500


# Import modules
import catalog.models

# Register blueprints
from views.api import api
from views.auth import auth
from views.data import data

app.register_blueprint(api)
app.register_blueprint(auth)
app.register_blueprint(data)
