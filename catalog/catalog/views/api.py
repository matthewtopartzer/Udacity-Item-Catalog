"""This module includes most of the routes for the app.

It includes endpoints for viewing and modifying the catalog.
"""

import httplib2
import requests
import json

from flask import abort
from flask import Blueprint
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import request
from flask import render_template
from flask import session
from flask import url_for

from sqlalchemy.orm.exc import NoResultFound

from catalog import app
from catalog import db
from catalog.models import Base, User, Category, Item
from catalog.forms import CSRFForm
from catalog.forms.item import ItemForm

from auth import login_required

api = Blueprint('api', __name__)


################################################################################
# View catalog
################################################################################

# Maximum number of recently created or modified items to show 
LATEST_ITEMS_TO_SHOW = 10

@api.route("/")
@api.route("/catalog/")
def view_catalog():
    """Catalog homepage."""
    categories = db.query(Category).all()
    items = db.query(Item).order_by(Item.name).all()
    latest_items = db.query(Item).order_by(Item.updated.desc()) \
        .limit(LATEST_ITEMS_TO_SHOW).all()
    return render_template("api/catalog.html", 
        categories = categories,
        items = items,
        latest_items = latest_items)


@api.route("/catalog/category/<int:category_id>/")
def view_category(category_id):
    """View a specific category."""
    try:
        category = db.query(Category).filter_by(id = category_id).one()
    except NoResultFound:
        abort(404)
    items = db.query(Item).filter_by(category_id = category.id)
    return render_template("api/category.html", category = category, items = items)


@api.route("/catalog/item/<int:item_id>/")
def view_item(item_id):
    """View a specific item."""
    try:
        item = db.query(Item).filter_by(id = item_id).one()
    except NoResultFound:
        abort(404)
    return render_template("api/item.html", item = item)


################################################################################
# Create/edit/delete items
################################################################################

@api.route("/catalog/item/new/", methods = ['GET', 'POST'])
@login_required
def new_item():
    """Create new item."""
    # populate form
    form = ItemForm(request.form)
    categories = db.query(Category).order_by(Category.name).all() # sort alphabetically
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # display and validate form    
    if request.method != 'POST' or not form.validate():
        return render_template('api/new_item.html', form = form)

    # get image file
    form_file = request.files[form.image.name]
    img_filename = None
    if form_file:
        filename = secure_filename(form_file.filename)
        filename = generate_unique_filename(filename)
        form_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_filename = filename

    # create item
    new_item = Item(
        name = form.name.data,
        description = form.description.data,
        category_id = form.category_id.data,
        image = img_filename,
        user_id = session['user_id'])
    db.add(new_item)
    db.commit()

    flash(message = "Item successfully created", category = "success")

    return redirect(url_for('api.view_item', item_id = new_item.id))

@api.route("/catalog/item/<int:item_id>/edit/", methods = ['GET', 'POST'])
@login_required
def edit_item(item_id):
    """Edit an item."""
    try:
        item = db.query(Item).filter_by(id = item_id).one()
    except NoResultFound:
        abort(404)

    # only author can edit item
    if item.user_id != session['user_id']:
        flash(message = "You are not allowed to update this item", category = "error")
        return render_template("api/item.html", item = item)

    # populate form
    form = ItemForm(request.form, item)
    categories = db.query(Category).order_by(Category.name).all() # sort alphabetically
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # display and validate form
    if request.method != 'POST' or not form.validate():
        return render_template('api/edit_item.html', form = form, item = item)

    # get image file
    form_file = request.files[form.image.name]
    img_filename = None
    if form_file:
        filename = secure_filename(form_file.filename)
        filename = generate_unique_filename(filename)
        form_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_filename = filename

    # edit item
    item.name = form.name.data
    item.description = form.description.data
    item.category_id = form.category_id.data
    # only replace image if new image is uploaded
    if img_filename:
        item.image = img_filename
    db.add(item)
    db.commit()

    flash(message = "Item successfully updated", category = "success")

    return redirect(url_for('api.view_item', item_id = item.id))

@api.route("/catalog/item/<int:item_id>/delete/", methods = ['GET', 'POST'])
@login_required
def delete_item(item_id):
    """Delete an item."""
    try:
        item = db.query(Item).filter_by(id = item_id).one()
    except NoResultFound:
        abort(404)

    # only author can delete item
    if item.user_id != session['user_id']:
        flash(message = "You are not allowed to remove this item", category = "error")
        return render_template("api/item.html", item = item)

    # populate form - just a base form here for csrf validation
    form = CSRFForm(request.form)

    # display and validate form
    if request.method != 'POST' or not form.validate():
        return render_template('api/delete_item.html', form = form, item = item)

    # delete the item
    db.delete(item)
    db.commit()

    flash(message = "Item successfully removed", category = "success")

    return redirect(url_for('api.view_catalog'))


################################################################################
# User info
################################################################################

@api.route("/user/profile/")
@login_required
def user_profile():
    """View current user's profile page."""
    user_id = session["user_id"]
    user = db.query(User).filter_by(id = user_id).one()
    # sort user items alphabetically 
    items = db.query(Item).filter_by(user_id = user_id).order_by(Item.name).all()
    return render_template("api/user.html", user = user, items = items)


################################################################################
# Image upload
################################################################################

import os
import datetime
import string
import random
import uuid
from werkzeug import secure_filename
from flask import send_from_directory

def generate_random_string():
    """Generate a random string with alphabetic characters and digits."""
    alpha = string.ascii_lowercase + string.ascii_uppercase + string.digits
    rand_str = "".join(random.choice(alpha) for x in xrange(32))
    return rand_str

def generate_unique_filename(original_filename):
    """Generate a unique name for a file.

    The current implementation does not actually guarantee uniqueness,
    but the probability of generating the same name twice is very low.

    The generated file names include the date and time, and a random UUID.

    Args:
      original_filename: the original name of the file.
    Returns:
      A file name with the same extension as the original file, and
      which is almost surely unique.
    """
    # keep file extension, in lower case
    ext = os.path.splitext(original_filename)[1].strip().lower()

    # current date and time
    date_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # generate random uuid
    uuid_hex = uuid.uuid4().hex

    filename = "_".join([date_time, uuid_hex, ext])
    return filename


@api.route("/image/<string:filename>/")
def view_image(filename):
    """View uploaded image."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_image_url(filename):
    """Get URL for an image file.

    If no file is specified, returns a URL for a place holder image.

    Note that this method does not check if the file actually exists.
    """
    if filename:
        return url_for("api.view_image", filename = filename)
    else:
        return "https://placehold.it/300x300.png?text=No+image"

################################################################################

# Expose utility functions to templates
# http://flask.pocoo.org/docs/0.10/templating/
@api.context_processor
def utility_processor():
    return dict(get_image_url = get_image_url)

################################################################################
