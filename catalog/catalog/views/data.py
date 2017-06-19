"""This module includes routes for getting data in special formats from the app.

It includes endpoints for getting catalog data in JSON format, and Atom feeds.
"""

from flask import abort
from flask import Blueprint

from sqlalchemy.orm.exc import NoResultFound

from catalog import db
from catalog.models import User, Category, Item

from auth import login_required

data = Blueprint('data', __name__)


################################################################################
# JSON
################################################################################

from flask import jsonify

@data.route('/catalog.json')
def view_catalog_json():
    """Catalog in json format."""
    categories = db.query(Category).all()
    items = db.query(Item).all()
    return jsonify(categories = [c.serialize for c in categories],
        items = [i.serialize for i in items])

@data.route("/catalog/category-<int:category_id>.json")
def view_category_json(category_id):
    """Category in json format."""
    try:
        category = db.query(Category).filter_by(id = category_id).one()
    except NoResultFound:
        abort(404)
    items = db.query(Item).filter_by(category_id = category.id).all()
    return jsonify(category = category.serialize,
        items = [i.serialize for i in items])

@data.route("/catalog/item-<int:item_id>.json")
def view_item_json(item_id):
    """Item in json format."""
    try:
        item = db.query(Item).filter_by(id = item_id).one()
    except NoResultFound:
        abort(404)
    return jsonify(item = item.serialize)

@data.route('/users.json')
@login_required
def users_json():
    """List of users in json format.

    This is for debugging and should probably be removed or protected.

    TODO (pt314): Remove or protect this endpoint.
    """
    users = db.query(User).all()
    return jsonify(users = [u.serialize for u in users])


################################################################################
# Atom
################################################################################
#
# See:
#
# Generating Feeds with Flask
# http://flask.pocoo.org/snippets/10/
#
# Atom Syndication
# http://werkzeug.pocoo.org/docs/0.11/contrib/atom/
#
################################################################################

from urlparse import urljoin
from flask import request
from flask import url_for
from werkzeug.contrib.atom import AtomFeed

# Number of items to include in atom feed
ATOM_FEED_SIZE = 5

def make_external(url):
    """Convert relative URL to absolute URL."""
    return urljoin(request.url_root, url)

@data.route('/recent.atom')
def recent_atom_feed():
    """Atom feed with recently created and updated items."""
    feed = AtomFeed('Latest Items', 
        feed_url = request.url, url = request.url_root)
    items = db.query(Item).order_by(Item.updated.desc()).limit(ATOM_FEED_SIZE).all()
    for item in items:
        item_url = url_for('api.view_item', item_id = item.id)
        feed.add(title = item.name,
                 content = unicode(item.name + " (" + item.category.name + "): " + item.description),
                 content_type = 'text',
                 author = item.user.name,
                 url = make_external(item_url),
                 updated = item.updated,
                 published = item.created)
    return feed.get_response()

################################################################################
