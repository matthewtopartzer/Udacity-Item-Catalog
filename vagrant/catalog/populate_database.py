from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog import db
from catalog.models import User, Category, Item


# Utility functions

def add_items(category, item_names):
	"""Add a list of items to a category."""
	for name in item_names:
		item = Item(name = name, category_id = category.id)
		db.add(item)
	db.commit()

def add_item(category, item):
    """Add an item to a category."""
    item.category_id = category.id
    db.add(item)
    db.commit()


# Sample user

user = User(name = "Werner Herzog",
    email = "werner@wernerherzog.com",
    picture = "http://i3.kym-cdn.com/entries/icons/original/000/019/530/2014_BAMPresents_WernerHerzog_613x463.jpg")  # NOQA

db.add(user)
db.commit()


# Sample categories

category1 = Category(name = "Simon & Garfunkel")
db.add(category1)

category2 = Category(name = "More Simon & Garfunkel")
db.add(category2)

category3 = Category(name = "Fruits & Vegetables")
db.add(category3)

category4 = Category(name = "More Fruits & Vegetables")
db.add(category4)

db.commit()


# Sample items

add_item(category1, Item(user = user, name = "Parlsey", description = "A biennial plant that will return to the garden year after year once it is established."))
add_item(category1, Item(user = user, name = "Sage", description = "A perennial, evergreen subshrub, with woody stems, grayish leaves."))
add_item(category1, Item(user = user, name = "Rosemary", description = "A woody, perennial herb with fragrant, evergreen, needle-like leaves."))

add_item(category2, Item(user = user, name = "Thyme", description = "An evergreen herb with culinary, medicinal, and ornamental uses."))
add_item(category2, Item(user = user, name = "Latte", description = "A coffee drink made with espresso and steamed milk."))
add_item(category2, Item(user = user, name = "Kale", description = "Kale is actually one of the healthiest and most nutritious foods on the planet."))

add_item(category3, Item(user = user, name = "Banana", description = "An edible fruit, botanically a berry, produced by several kinds of large herbaceous flowering plants in the genus Musa."))
add_item(category3, Item(user = user, name = "Cabbage", description = "A leafy green or purple biennial plant, grown as an annual vegetable crop for its dense-leaved heads."))
add_item(category3, Item(user = user, name = "Potato", description = "A starchy, tuberous crop from the perennial nightshade Solanum tuberosum."))

add_item(category4, Item(user = user, name = "Lettuce", description = "An annual plant of the daisy family."))
add_item(category4, Item(user = user, name = "Onion", description = "A vegetable and is the most widely cultivated species of the genus Allium."))
add_item(category4, Item(user = user, name = "Orange", description = "The fruit of the Citrus."))
