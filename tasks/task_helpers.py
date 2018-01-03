import glob
import inspect
import ntpath
import time

import requests
import yaml
from colored import stylize, fg
from invoke import UnexpectedExit
from invoke import run
from requests.exceptions import ConnectionError
from retrying import retry

from .configurable_globals import *


MIGRATION_ENV_PARAM_TEMPLATE = "{key}{delim}'{value}'"


def retry_if_connection_error(exception):
    return isinstance(exception, ConnectionError)


retry_options = dict(retry_on_exception=retry_if_connection_error,
                     stop_max_delay=60000,
                     wait_fixed=2000)


@retry(**retry_options)
def wait_for_server_to_be_up():
    requests.get("http://localhost:9000/healthcheck")


def print_test_header():
    test_group_name = inspect.stack()[0][3]
    print(stylize("\n\t\t\t-- Running {} --\n".format(test_group_name), fg("white")),
          flush=True)


def set_tag(target_build, new_tag):
    run("docker tag kenshoo-docker.jfrog.io/{app_name}:{target} "
        "kenshoo-docker.jfrog.io/{app_name}:{new_tag}".format(app_name=APP_NAME,
                                                              target=target_build,
                                                              new_tag=new_tag))

def get_next_revision_id():
    versions_path = "{migration_dir}/versions/*.py".format(migration_dir=MIGRATIONS_DIR)
    get_previous_revision_ids = (int(ntpath.basename(mig).split("_", 1)[0])
                                 for mig in glob.glob(versions_path))
    last_rev = max(get_previous_revision_ids, default=0)
    return last_rev + 1


def init_invoke_yaml():
    invoke_config = load_invoke_data()
    configure_invoke_yaml(invoke_config)


def load_invoke_data():
    try:
        with open(TASK_CONFIGURATION_FILE) as invoke_file:
            return yaml.load(invoke_file)
    except FileNotFoundError:
        return {}


def configure_invoke_yaml(previous_config):
    with open(TASK_CONFIGURATION_FILE, 'w') as invoke_file:
        new_password = get_user_input()
        previous_config['artifactory_microcosm_password'] = new_password
        yaml.dump(previous_config, invoke_file, default_flow_style=False)


def get_user_input():
    return input("What is the ARTIFACTORY_PASSWORD? \n")


def prepare_migrate_env_params(params, delim="="):
    return " ".join(MIGRATION_ENV_PARAM_TEMPLATE.format(key=key, delim=delim, value=value)
                    for key,value in params.items())


def db_migration_command(msg, command="migrate"):
    ts1, ts2 = str(time.time()).split(".")
    revision_id = get_next_revision_id()
    params = prepare_migrate_env_params({"--rev-id": "{rev_id}_{ts1}.{ts2}".format(
                                                                    rev_id=revision_id,
                                                                    ts1=ts1,
                                                                    ts2=ts2),
                                         "--message":msg},
                                        delim=" ")
    return db_command(command, params=params)


def db_command(command, params= "", env_vars=ENV_PARAMS):
    env_params = prepare_migrate_env_params(env_vars)
    manage_script = path.join(FILE_DIRNAME, 'manage.py')
    return "{env} python {manage} db {cmd} {params}".format(env=env_params,
                                                            manage=manage_script,
                                                            cmd=command,
                                                            params=params)


def db_upgrade_command():
    return db_command("upgrade")


def wait_mysql_is_up():
    print("waiting for mysql")
    def waiter():
        print(".",)
        run("mysql -u{user} -p{password} -h{host} -P{port} "
            "--protocol=tcp -e 'select \".\"' 2>/dev/null".format(user=DB_USER,
                                                                  password=DB_PASS,
                                                                  host=DB_HOST,
                                                                  port=DB_PORT))
    wait(waiter)
    print("mysql is up")


@retry(stop_max_attempt_number=20, wait_fixed=1000)
def wait(waiter):
    waiter()


def login_needed():
    try:
        run("cat {home}/.docker/config.json | grep -q '{artifactory_url}' ".format(
                                                home=HOME_DIR,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))
        return False
    except UnexpectedExit:
        return True
