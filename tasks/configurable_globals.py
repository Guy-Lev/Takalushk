import os
from os import path

FILE_DIRNAME = os.path.dirname(os.path.realpath(__file__))
MIGRATIONS_DIR = os.path.join(FILE_DIRNAME, os.pardir, 'app/migrations/')
LOGS_DIR = os.path.join(FILE_DIRNAME, os.pardir, 'app/logs/')

# These globals should be changed accordingly
APP_ROOT = 'app'
APP_NAME = 'python_template'
LINE_COVERAGE_MIN_THRESHOLD = 80
TASK_CONFIGURATION_FILE = path.expanduser('~/.invoke.yaml')

#STAGING ENV
STAGING_LABEL = "staging"
STAGING_URL = "https://{app_name}-staging.kenshoo-lab.com".format(app_name=APP_NAME)
STAGING_PLACEMENT = "labs_east"

#PRODUCTION ENV
PRODUCTION_LABEL = "prod"
PRODUCTION_URL = "https://{app_name}-prod.kenshoo-prod.com".format(app_name=APP_NAME)
PRODUCTION_PLACEMENT = "prod_east"


RDS_PORT = "RDS_PORT"
RDS_HOSTNAME = "RDS_HOSTNAME"
RDS_PASSWORD = "RDS_PASSWORD"
RDS_USERNAME = "RDS_USERNAME"

DB_PORT = os.environ.get(RDS_PORT, "33060")
DB_HOST = os.environ.get(RDS_HOSTNAME, "localhost")
DB_PASS = os.environ.get(RDS_PASSWORD, "root")
DB_USER = os.environ.get(RDS_USERNAME, "root")

ENV_PARAMS = {RDS_USERNAME: DB_USER,
              RDS_PASSWORD: DB_PASS,
              RDS_HOSTNAME: DB_HOST,
              RDS_PORT: DB_PORT,
              "RDS_DB_NAME": "app",
              "APP_NAME": APP_NAME,
              "ENVIRONMENT_TYPE": "default",
              "LOG_FILE": "{dir}/{log}".format(dir=LOGS_DIR, log="app.log")}
BUILD_PROMOTED = 'BUILD_WAS_PROMOTED'
DEPLOYMENT_SUCCESS = 'DEPLOYMENT_SUCCESS'
ENV_PROPERTIES_FILE_NAME = 'environment.properties'
ARTIFACTORY_DOCKER_REPO = "kenshoo-docker.jfrog.io"
HOME_DIR = path.expanduser("~")
