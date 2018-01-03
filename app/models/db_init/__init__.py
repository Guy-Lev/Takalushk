import os
from operator import itemgetter

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.conf import conf
from ...app_init import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    *itemgetter('username',
                'password',
                'host',
                'port',
                'dbname')(conf["rds"]))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

DB = SQLAlchemy(app)

FILE_DIRNAME = os.path.dirname(os.path.realpath(__file__))
MIGRATIONS_DIR = os.path.join(FILE_DIRNAME, os.pardir, os.pardir, 'migrations/')
migrate = Migrate(app, DB, directory=MIGRATIONS_DIR)
