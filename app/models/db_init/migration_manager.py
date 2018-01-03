from flask_migrate import upgrade

from app.conf import *


def db_upgrade(app):
    rev_id = conf["rds"]["revid"]
    with app.app_context():
        upgrade(revision=rev_id)
