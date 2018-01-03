import logging
from logging.config import fileConfig
from os import path

from flasgger import Swagger, swag_from

from app.conf import conf
from app.controllers.metrics_controller import MetricsController
from app.lib.performance_metrics import register_metrics_reporter
from app.routes import create_routes
from .app_init import app
from .controllers.response_builder import ok

logging_ini_file = path.join(path.dirname(path.realpath(__file__)), 'logging.ini')
fileConfig(logging_ini_file, disable_existing_loggers=False)
logger = logging.getLogger(__name__)
swagger = Swagger(app)


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

# If there is no Database remove the following lines
from .models import create_db, db_upgrade
create_db(app)
db_upgrade(app)

