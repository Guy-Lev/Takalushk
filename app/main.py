import logging
from logging.config import fileConfig
from os import path

from flasgger import Swagger, swag_from
from app.conf import conf
from app.controllers.metrics_controller import MetricsController
from app.lib.performance_metrics import register_metrics_reporter
from app.routes import create_routes
from .app_init import app
from github import Github
from .controllers.response_builder import ok

logging_ini_file = path.join(path.dirname(path.realpath(__file__)), 'logging.ini')
fileConfig(logging_ini_file, disable_existing_loggers=False)
logger = logging.getLogger(__name__)
swagger = Swagger(app)
from .models.db_init import DB


create_routes(app, metrics=MetricsController())

@app.before_first_request
def initial_configuration():
    # The following environment variables must be instantiated for your hosted graphite
    # reporting. APP_NAME may possibly be instantiated automatically on AWS Elastic
    # Beanstalk.
    # These values should be adjusted per environment (development, staging/lab, and
    # production).
    # Change this code if you do not want these configuration details to be derived from
    # environment variables.
    # The parameters here and the logic in which to derive their values should be changed
    # based on your needs.
    # The endpoint argument should be kenshoo.carbon.hostedgraphite.com.
    # The token should either be f205c253-320d-4d92-8e7d-ce8d125d5cf1 for staging or
    # c273ef2c-40a7-49b8-84bf-991ef9353b97 for production.
    graphite_conf = conf['graphite']
    if graphite_conf['reporting_enabled']:
        register_metrics_reporter(interval=graphite_conf['reporting_interval'],
                                  app_prefix=conf["app"]["name"],
                                  endpoint=graphite_conf['reporting_endpoint'],
                                  token=graphite_conf['reporting_token'])

@app.route("/")
def hello():
    logger.info("Hello world run...")
    return "Hello World!"


@app.route('/healthcheck')
@swag_from('swagger/healthcheck.yml')
def healthcheck():
    return ok({"message": "OK"})

class testCounter:
    def __init__(self, name):
        self.name = name
        self.count = 0


g = Github("c7809e9a93587a4cb4482335c2fd73326a01b129")
org = g.get_organization('Kenshoo')
main_dict = {}

@app.route("/init_from_github/<int:count_to_init>")
def init_from_github(count_to_init):
    logger.info("Initializing from github...")
    repo = org.get_repo('Search')
    count = 0
    for pull in repo.get_pulls('all'):
        files = get_files_from_pull(pull)
        tests = get_tests_from_pull(pull)
        count_tests_for_files(files, tests)
        if count > count_to_init:
            break
        count = count + 1
        if count % 10 == 0:
            print(count)
    logger.info("Initializing from github done!")
    return "Initialized last " + str(count_to_init) + " pulls from github!"

# If there is no Database remove the following lines
from .models import create_db, db_upgrade
create_db(app)
db_upgrade(app)


def get_tests_from_pull(pull):
    test_set = set()
    for comment in pull.get_issue_comments():
        c = comment.body
        if c.startswith("test ") and c.endswith(" please"):
            c = c[5:-7]
            tests = c.split()
            test_type = "integration"
            if "cucumber" in tests:
                test_type = "cucumber"
            for test in tests:
                if test not in ["cucumber", "integration"]:
                    test_set.add(test + " " + test_type)
    if test_set:
        print(test_set)
    return test_set

def get_files_from_pull(pull):
    files_set = set()
    for f in pull.get_files():
        files_set.add(f._filename.value)
    return files_set

def count_tests_for_files(files, tests):
    if len(files) == 0 or len(tests) == 0:
        return
    for f in files:
        if f not in main_dict:
            main_dict[f] = {}
        for t in tests:
            if t not in main_dict[f]:
                main_dict[f][t] = 1
            else:
                main_dict[f][t] = main_dict[f][t] + 1


@app.route("/get_top/<int:prid>/")
def get_top(prid):
    test_count = {}
    logger.info("get_top")
    repo = org.get_repo('Search')
    files = get_files_from_pull(repo.get_pull(prid))
    for f in files:
        if f not in main_dict:
            continue

        for test in main_dict[f].items():
            name = test[0]
            count = test[1]
            if name not in test_count:
                test_count[name] = 0
            test_count[name] = test_count[name] + main_dict[f][name]
    top = sorted(test_count.keys(), key=lambda x: x[1], reverse=True)
    ret = ""
    for test in top:
        ret += test + ","
    return ret[:-1]


