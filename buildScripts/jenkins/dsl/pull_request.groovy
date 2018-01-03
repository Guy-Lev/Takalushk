def NAME = "APPLICATION"
def EMAIL = "TEAM@kenshoo.com"
def JOB_NAME = "${NAME}-pull-request"

job(JOB_NAME) {
    label("microcosm-centos7")

    logRotator(10,10)
    concurrentBuild(true)

    throttleConcurrentBuilds{
        maxPerNode 1
        maxTotal 10
    }

    scm {
        git {
            remote {
                url("git@github.com:kenshoo/${NAME}.git")
                credentials('3f510033-65a9-4afd-9851-c7359bd3f9db')
                refspec('+refs/pull/*:refs/remotes/origin/pr/*')
            }

            configure { node ->
                node / 'extensions' / 'hudson.plugins.git.extensions.impl.CleanBeforeCheckout' {}
            }

            branch("\${sha1}")
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
          absolute(5)
        }
    }

    triggers {
        pullRequest {
            orgWhitelist('Kenshoo')
            useGitHubHooks()
        }
    }

    steps {
      shell("""
          virtualenv -p python3.4 venv
          source venv/bin/activate
          pip install -r requirements-dev.txt -r requirements.txt --extra-index-url="https://jenkins:\${AWS_ARTIFACTORY_PASS}@artifactory.kenshoo-lab.com/artifactory/api/pypi/PyPI-releaes/simple/" --trusted-host artifactory.kenshoo-lab.com
          invoke clean test
      """)
    }

    publishers {
        postBuildScripts {
            steps {
                shell("""
                    source venv/bin/activate
                    invoke clean
                """)
            }
        }
        archiveJunit('build/*test-results.xml')

        cobertura('build/unit_coverage.xml') {}

        violations() {
     		pylint(0, 1, 1, 'build/pylint.log')
  		}

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
