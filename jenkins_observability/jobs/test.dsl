NAME = 'test-pipeline'
DSL = '''pipeline {
    agent any
    environment {
        HOME = "${env.WORKSPACE}"
    }

    stages {
        stage('Hello World') {
            steps {
                echo 'Hello, Jenkins Pipeline!'
                sh 'echo "Current user: $(whoami)"'
                sh 'echo "Current directory: $(pwd)"'
                sh 'ls -la'
            }
        }

        stage('Environment Info') {
            steps {
                sh '''
                    echo "=== Environment Information ==="
                    echo "JOB_NAME: ${JOB_NAME}"
                    echo "BUILD_NUMBER: ${BUILD_NUMBER}"
                    echo "WORKSPACE: ${WORKSPACE}"
                    echo "NODE_NAME: ${NODE_NAME}"
                    echo "JAVA_HOME: ${JAVA_HOME}"
                    echo "PATH: ${PATH}"
                '''
            }
        }

        stage('Simple Test') {
            steps {
                sh '''
                    echo "Running simple test..."
                    if [ -f "README.md" ]; then
                        echo "README.md exists"
                    else
                        echo "README.md not found"
                    fi
                '''
            }
        }

        stage('Archive Results') {
            steps {
                sh 'echo "Test results" > test-output.txt'
                archiveArtifacts artifacts: 'test-output.txt', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed'
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
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
