from os import environ

from invoke import call
from invoke import task, Collection

from .task_helpers import *

@task
def init_local_env(ctx):
    ''':Local Dev task: Add microservice context parameters to invoke file'''
    init_invoke_yaml()


@task
def clean(ctx,stage="before"):
    '''Clean application's produced processes, files, and the like'''
    run("docker-compose kill", echo=True)
    run("docker-compose rm -f", echo=True)
    run("docker rm -f app app_db", echo=True, warn=True)
    run("docker rmi app", echo=True, warn=True)


@task
def docker_artifactory_login(ctx):
    '''Login to artifactory'''
    try:
        if login_needed():
            run("docker login -u {user} -p {password} {artifactory_url}".format(
                                            user=ctx.artifactory_user,
                                            password=ctx.artifactory_password,
                                            artifactory_url=ARTIFACTORY_DOCKER_REPO))
    except UnexpectedExit as auth_error:
        password = getattr(ctx, 'artifactory_password', None)[-4:]
        password = '****' + password if password else "None provided"

        print("Could not login to Artifactory.\n"
              "Your credentials are 'user={user} pass={password}'\n"
              "Make sure you provide a username and password to login to artifactory.\n"
              "If this is your first time running your application then please run the\n"
              "environment setup task => `invoke init_local_env`".format(
                        user=ctx.artifactory_user,
                        password=password))
        raise auth_error


@task(pre=[docker_artifactory_login], aliases=["build"])
def build_local_app(ctx):
    '''Build local instance of application in docker with associated DB'''
    run('docker build . -t app', echo=True)
    run('docker-compose up -d  && docker-compose logs -f --tail="all" &', echo=True)
    wait_for_server_to_be_up()


@task(default=True)
def unit_test(ctx):
    '''Run unit tests with coverage'''
    print_test_header()
    run("py.test {app_root}/tests --cov={app_root} "
        "--cov-report=term --cov-report=xml "
        "--cov-fail-under={line_coverage}".format(
                                app_root=APP_ROOT,
                                line_coverage=LINE_COVERAGE_MIN_THRESHOLD))


@task
def smoke_test(ctx):
    '''Run smoke test suite on actual living application'''
    print_test_header()
    run("py.test --url={url} {app_root}/integration_tests/smoke".format(
                                                            url=ctx.url,
                                                            app_root=APP_ROOT))


@task(pre=[build_local_app])
def accept_test(ctx):
    '''Run acceptance test suite on docker instance'''
    print_test_header()
    run("py.test {app_root}/integration_tests/acceptance".format(app_root=APP_ROOT))


@task(pre=[unit_test, accept_test])
def test(ctx):
    pass



@task
def api_test(ctx):
    '''Run API test suite to insure external API expectations'''
    print_test_header()
    run("py.test {app_root}/integration_tests/api".format(app_root=APP_ROOT))


@task(pre=[docker_artifactory_login])
def create_build(ctx, tag):
    '''Create new version of apllication docker image'''
    try:
        run("docker pull {artifactory_url}/{app_name}:latest".format(
                                                app_name=APP_NAME,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))
    except UnexpectedExit:
        print("Latest image for {app_name} does not exist.\n"
              "Skipping pull for latest.".format(app_name=APP_NAME))

    run("docker build -t {artifactory_url}/{app_name}:{tag} .".format(
                                                app_name=APP_NAME,
                                                tag=tag,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))
    run("docker push {artifactory_url}/{app_name}:{tag}".format(
                                                app_name=APP_NAME,
                                                tag=tag,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))


@task(aliases=["deploy"])
def deploy_current_build(ctx, build):
    '''Deploy application docker image'''
    run("micro version --placement {placement} --app {app_name} "
        "--label {label} --version {build_number} --yes".format(
                                                            placement=ctx.placement,
                                                            app_name=APP_NAME,
                                                            label=ctx.label,
                                                            build_number=build))
    run("micro status --placement {placement} --app {app_name} "
        "--label {label} --wait_for READY".format(placement=ctx.placement,
                                                  label=ctx.label,
                                                  app_name=APP_NAME))


@task
def promote_build(ctx, build):
    '''Push built docker image with build number as tag'''
    set_tag(build, build + '-promoted')
    set_tag(build, 'latest')
    run("docker push {artifactory_url}/{app_name}".format(
                                                app_name=APP_NAME,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))


@task(pre=[docker_artifactory_login])
def rollback_to_last_stable(ctx, build):
    '''Rollback deployed apllication image version to a previous version'''
    run("docker pull {artifactory_url}/{app_name}:{last_stable_build}".format(
                                                app_name=APP_NAME,
                                                last_stable_build=build,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))
    set_tag(build, 'latest')
    run("docker push {artifactory_url}/{app_name}".format(
                                                app_name=APP_NAME,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))


@task(pre=[docker_artifactory_login])
def demote_build(ctx, build):
    ''':Jenkins job task: to demote a failed promoted build'''
    if environ.get(DEPLOYMENT_SUCCESS, 'false') == 'false' and \
                    environ.get(BUILD_PROMOTED, 'false') == 'true':
        set_tag('latest', build)
        run("docker push {artifactory_url}/{app_name}:{new_latest_tag}".format(
                                                app_name=APP_NAME,
                                                new_latest_tag=build,
                                                artifactory_url=ARTIFACTORY_DOCKER_REPO))

@task()
def db_upgrade(ctx, user, pwd, host, port=3306):
    env = dict(ENV_PARAMS)
    env.update({RDS_USERNAME: user, RDS_PASSWORD: pwd, RDS_HOSTNAME: host, RDS_PORT: port})
    print("*************** upgrade dry run ***************")
    run(db_command(command="upgrade", params="--sql", env_vars=env), echo=True)
    print("*************** upgrade run ***************")
    run(db_command(command="upgrade", env_vars=env), echo=True)

@task(pre=[call(clean,"before"),])
def db_baseline(ctx):
    run("docker-compose up -d mysql", echo=True)
    wait_mysql_is_up()
    run(db_upgrade_command(), echo=True)

@task(pre=[db_baseline], post=[call(clean,"after")])
def db_migrate(ctx, msg):
    """create revision migration script according to schema changes"""
    run(db_migration_command(msg=msg), echo=True)

@task(pre=[db_baseline], post=[call(clean,"after")])
def db_migrate_custom(ctx, msg):
    """create a customized revision migration script (empty for manual script)"""
    run(db_migration_command(command="revision",msg=msg))

###############################
### Namespace Instantiation ###
###############################

platform_based_tasks = (smoke_test, deploy_current_build)

staging = Collection('staging')
# url must be updated with actual staging/production URL
staging.configure({'placement': STAGING_PLACEMENT,
                   'label': STAGING_LABEL,
                   'post_success_flag': BUILD_PROMOTED,
                   'url': STAGING_URL})

prod = Collection('production')
prod.configure({'placement': PRODUCTION_PLACEMENT,
                'label': PRODUCTION_LABEL,
                'post_success_flag': DEPLOYMENT_SUCCESS,
                'url': PRODUCTION_URL})

for plaform_task in platform_based_tasks:
    staging.add_task(plaform_task)
    prod.add_task(plaform_task)

namespace = Collection(staging,
                       prod,
                       clean,
                       init_local_env,
                       docker_artifactory_login,
                       test,
                       unit_test,
                       api_test,
                       accept_test,
                       build_local_app,
                       create_build,
                       promote_build,
                       rollback_to_last_stable,
                       demote_build,
                       db_migrate,
                       db_baseline,
                       db_migrate_custom,
                       db_upgrade)

default_configuration = {"artifactory_user": 'microcosm',
                         "artifactory_password": environ.get(
                                                "ARTIFACTORY_MICROCOSM_PASSWORD", None)}

namespace.configure(default_configuration)
