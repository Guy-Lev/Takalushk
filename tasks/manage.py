import sys, os
FILE_DIRNAME = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(FILE_DIRNAME, os.pardir))
from flask_migrate import MigrateCommand
from flask_script import Manager

from app.app_init import app as flask_app
# noinspection PyUnresolvedReferences
from app.models.glob_models import *

from app.models import create_db
create_db(flask_app)

manager = Manager(flask_app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()

