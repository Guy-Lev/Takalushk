def NAME = "APPLICATION"
def BRANCH_NAME = "master"
def EMAIL = "TEAM@kenshoo.com"
def JOB_NAME = "${NAME}-rollback"
def MAX_NUMBER_OF_VERSIONS = 10

job(JOB_NAME) {
    label("microcosm-centos7")

    logRotator(-1,10)
    concurrentBuild(false)

    scm {
        git {
            remote {
                url("git@github.com:kenshoo/${NAME}.git")
                credentials('3f510033-65a9-4afd-9851-c7359bd3f9db')
                refspec("+refs/heads/${BRANCH_NAME}:refs/remotes/origin/${BRANCH_NAME}")
            }

            configure { node ->
                node / 'extensions' / 'hudson.plugins.git.extensions.impl.CleanBeforeCheckout' {}
            }

            branch(BRANCH_NAME)
        }
    }

    configure { project ->
        def properties = project / 'properties'
        properties<< {
            'com.coravy.hudson.plugins.github.GithubProjectProperty'{
                projectUrl "https://github.com/kenshoo/${NAME}/"
            }
        }
    }

    parameters {
            activeChoiceParam('SelectedBuild') {
            description('The desired previous stable build')
            filterable()
            choiceType('SINGLE_SELECT')
            scriptlerScript('get_app_docker_versions.groovy'){
                parameter('app_name', '${NAME}')
                parameter('max_num_of_versions', '$MAX_NUMBER_OF_VERSIONS')
            }
        }
    }

    wrappers {
        preBuildCleanup()
        timestamps()
        injectPasswords()
        colorizeOutput()
        timeout {
          absolute(10)
        }
        credentialsBinding {
            usernamePassword('DEPLOYER_USER', 'MICROCOSM_TOKEN', 'MICROCOSM_TOKEN')
        }        
    }

    steps {
        shell("""
        virtualenv -p python3.4 venv
        source venv/bin/activate

        pip install -r requirements-dev.txt -r requirements.txt --extra-index-url="https://jenkins:\${AWS_ARTIFACTORY_PASS}@artifactory.kenshoo-lab.com/artifactory/api/pypi/PyPI-releaes/simple/" --trusted-host artifactory.kenshoo-lab.com

        invoke staging.deploy --build=\$SelectedBuild
        invoke staging.smoke_test

        invoke production.deploy --build=\$SelectedBuild
        invoke production.smoke_test

        invoke rollback_to_last_stable --build=\$SelectedBuild
        """)

    }

    publishers {
        extendedEmail("${EMAIL}") {
            trigger(triggerName: 'Unstable',
                    sendToDevelopers: true, sendToRequester: true, includeCulprits: true, sendToRecipientList: false)
            trigger(triggerName: 'Failure',
                    sendToDevelopers: true, sendToRequester: true, includeCulprits: true, sendToRecipientList: false)
            trigger(triggerName: 'StatusChanged',
                    sendToDevelopers: true, sendToRequester: true, includeCulprits: true, sendToRecipientList: false)
            configure { node ->
                node / contentType << 'text/html'
            }
        }
    }
}
