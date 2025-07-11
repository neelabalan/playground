NAME = 'ecgo-docker-pipeline'
DSL = '''pipeline {
    agent {
        docker {
            image 'cibase:latest'
            args '-v /var/run/docker.sock:/var/run/docker.sock --privileged --user root'
        }
    }
    environment {
        HOME = "${env.WORKSPACE}"    
    }
    
    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                git url: 'https://github.com/neelabalan/ecgo.git', branch: 'main'
            }
        }
        stage('Test Shell') {
            steps {
                sh 'echo "Hello from $(whoami)"'
            }
        }
        stage('Docker build') {
            steps {
                script {
                    println "Workspace: ${WORKSPACE}"
                    sh 'ls'
                    sh 'make docker-build-local'
                }
            }
        }
        stage('Docker test') {
            steps {
                script {
                    sh 'make docker-test-local'
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'ecgo/bin/**', allowEmptyArchive: true
            archiveArtifacts artifacts: 'ecgo/coverage/**', allowEmptyArchive: true
        }
    }
}'''

pipelineJob(NAME) {
    definition {
        cps {
            script(DSL.stripIndent())
        }
    }
}