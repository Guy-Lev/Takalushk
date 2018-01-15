from github import Github
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
g = Github("")
org = g.get_organization('Kenshoo')
repo = org.get_repo('Search')
