from sqlalchemy_utils import create_database, database_exists
from . import DB

def create_db(app):
    engine = DB.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    if not database_exists(engine.url):
        create_database(engine.url)
