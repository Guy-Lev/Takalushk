import logging
import functools
from logging.config import fileConfig
from os import path

from flasgger import Swagger, swag_from
from .commons import db, org
from .learning_task import LearningTask
from app.conf import conf
from app.controllers.metrics_controller import MetricsController
from app.lib.performance_metrics import register_metrics_reporter
from app.routes import create_routes
from .app_init import app
from .controllers.response_builder import ok, bad_request, not_found
from .models.schema import File, Test, HandledPull, TestCount, Repo
from .models import create_db, db_upgrade
from flask import request
create_db(app)
db_upgrade(app)

logging_ini_file = path.join(path.dirname(path.realpath(__file__)), 'logging.ini')
fileConfig(logging_ini_file, disable_existing_loggers=False)
logger = logging.getLogger(__name__)
swagger = Swagger(app)


def commit_session(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        db.session.commit()  # disable REPEATABLE READ isolation level
        return f(*args, **kwargs)

    return wrapper

create_routes(app, metrics=MetricsController())

@app.before_first_request
def initial_configuration():
    graphite_conf = conf['graphite']
    if graphite_conf['reporting_enabled']:
        register_metrics_reporter(interval=graphite_conf['reporting_interval'],
                                  app_prefix=conf["app"]["name"],
                                  endpoint=graphite_conf['reporting_endpoint'],
                                  token=graphite_conf['reporting_token'])

@app.route('/healthcheck')
@swag_from('swagger/healthcheck.yml')
def healthcheck():
    return ok({"message": "OK"})

class testCounter:
    def __init__(self, name):
        self.name = name
        self.count = 0

task = LearningTask()


@app.route("/load", methods=["POST"])
@swag_from('swagger/load.yml')
def load_from_github():
    repo_name = request.args.get('repo', 'Search')
    direction = request.args.get('direction', 'asc')
    stop_on_handled = False if request.args.get('stop_on_handled') in ['false', 'False'] else True
    logger.info("loading pulls from {} stop_on_handled: {} direction:{}".format(repo_name, stop_on_handled, direction))
    msg = task.load_pulls(stop_on_handled=stop_on_handled, direction=direction, repo_name=repo_name)
    return ok({"message" : msg, "repo" : repo_name, "direction" : direction, "stop_on_handled" : stop_on_handled})


@app.route("/count_handled")
@commit_session
def count_handled_pulls():
    repo_name = request.args.get('repo', 'Search')
    handled_pulls = db.session.query(HandledPull).join(Repo).filter(Repo.id == HandledPull.repo_id, Repo.name == repo_name).count()
    msg = "TakalushK handled {} pull requests in {} so far.".format(str(handled_pulls), repo_name)
    return ok({"message" : msg})


@app.route("/top")
@commit_session
def get_top():
    repo_name = request.args.get('repo', 'Search')
    prid = request.args.get('prid')
    if not prid:
        return bad_request({"message" : "prid param is required"})
    try:
        repo = org.get_repo(repo_name)
        pull = repo.get_pull(int(prid))
    except Exception as e:
        return not_found({"message" :"Could not find pull request with id {} in {}".format(prid, repo_name), "github-error" : str(e) })

    file_paths = [f._filename.value for f in pull.get_files()]
    tests = db.session.query(Test).join(TestCount).join(File).join(Repo)\
        .filter(File.path.in_(file_paths), File.id == TestCount.file_id,
                Test.id == TestCount.test_id, File.repo_id == Repo.id, Repo.name == repo_name)\
        .order_by(TestCount.count.desc()).all()

    return ok({"repo" : repo_name, "prid" : prid, "tests" : [test.name + " " + test.type for test in tests]})


