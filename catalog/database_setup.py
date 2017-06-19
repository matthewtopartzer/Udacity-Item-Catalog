from catalog import engine
from catalog.models import Base

##### create database #####
Base.metadata.create_all(engine)
