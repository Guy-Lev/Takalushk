def NAME = "APPLICATION"
def BRANCH_NAME = "master"
def EMAIL = "TEAM@kenshoo.com"
def SLACK_CHANNEL = "team-channel" // modify or remove slack notify from DSL

def JOB_NAME = "${NAME}-release"

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

    triggers {
      githubPush()
    }

    steps {
        shell("""
        virtualenv -p python3.4 venv
        source venv/bin/activate

        pip install -r requirements-dev.txt -r requirements.txt --extra-index-url="https://jenkins:\${AWS_ARTIFACTORY_PASS}@artifactory.kenshoo-lab.com/artifactory/api/pypi/PyPI-releaes/simple/" --trusted-host artifactory.kenshoo-lab.com

        invoke clean test

        invoke create_build --tag \${BUILD_NUMBER}

        invoke staging.deploy --build=\$BUILD_NUMBER
        invoke staging.smoke_test

        invoke production.deploy --build=\$BUILD_NUMBER
        invoke production.smoke_test

        invoke promote_build --build=\$BUILD_NUMBER
        """)
    }

    publishers {
        // Beginnig of slack notify section, remove if you don't have or want to send notifications to channel
        slackNotifications {
            projectChannel("${SLACK_CHANNEL}")
            notifyFailure()
            notifyBackToNormal()
            includeTestSummary()
        }
        // end of slack notify section
        
        archiveJunit('build/*test-results.xml')

        cobertura('build/unit_coverage.xml') {}

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

        postBuildScripts {
            steps {
                shell("""
                source venv/bin/activate
                invoke clean
                """)
            }
            onlyIfBuildSucceeds(false)
            onlyIfBuildFails()
        }
    }
}
