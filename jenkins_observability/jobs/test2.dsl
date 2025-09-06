NAME = 'test2_pipeline'
DSL = '''pipeline {
    agent any
    environment {
        HOME = "${env.WORKSPACE}"
    }

    stages {
        stage('Build Simulation') {
            steps {
                script {
                    def duration = new Random().nextInt(120) + 60  // Random sleep between 60-180 seconds
                    echo "Simulating build for ${duration} seconds"
                    sleep(time: duration, unit: 'SECONDS')
                }
            }
        }

        stage('Random Failure Check') {
            steps {
                script {
                    if (new Random().nextBoolean()) {
                        error('Random failure occurred during build')
                    } else {
                        echo 'Build succeeded'
                    }
                }
            }
        }

        stage('Archive Results') {
            steps {
                sh 'echo "Build completed" > build-output.txt'
                archiveArtifacts artifacts: 'build-output.txt', allowEmptyArchive: true
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
