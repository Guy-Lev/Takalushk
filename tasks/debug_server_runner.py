import os
import sys
from subprocess import call

from tasks import wait_mysql_is_up, ENV_PARAMS


def start_mysql_docker():
    call(["docker", "rm", "-f", "app"])
    call(["docker-compose", "up", "-d", "mysql"])



def mock_api(args):
    if "--live" not in args:
        pass


def run_app():
    app.run(port=7917, host="0.0.0.0")


if __name__ == '__main__':
    os.environ.update(ENV_PARAMS)
    start_mysql_docker()
    wait_mysql_is_up()
    mock_api(sys.argv)
    from app.main import app

    run_app()

