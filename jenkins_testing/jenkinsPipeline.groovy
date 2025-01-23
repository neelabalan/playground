def call() {
    pipeline {
        agent any

        environment {
            GREETING = "Hello"
        }

        stages {
            stage('Build') {
                steps {
                    script {
                        if (env.BRANCH_NAME == 'main') {
                            echo "${GREETING} from main branch"
                            sh 'echo "Building main branch..."'
                        } else {
                            echo "${GREETING} from ${env.BRANCH_NAME}"
                            // Simulated build for non-main branch
                            sh "echo \"Building branch ${env.BRANCH_NAME}...\""
                        }
                    }
                }
            }

            stage('Test') {
                when {
                    expression {
                        return env.EXECUTE_TESTS == 'true'
                    }
                }
                steps {
                    echo "Executing tests..."
                    sh 'echo "Running unit tests..."'
                }
            }

            stage('Deploy') {
                steps {
                    echo "Deploy stage"
                    sh 'echo "Deploying application..."'
                }
            }
        }
    }
}
