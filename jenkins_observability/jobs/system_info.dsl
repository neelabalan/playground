NAME = 'system_info'
DSL = '''pipeline {
  agent any
  stages {
    stage('System Information') {
      steps {
        sh 'echo "=== System Information ==="'
        sh 'uname -a'
        sh 'echo "Current user: $(whoami)"'
        sh 'echo "Current directory: $(pwd)"'
        sh 'echo "Available disk space:"'
        sh 'df -h'
        sh 'echo "Memory information:"'
        sh 'free -h'
      }
    }
    stage('Environment Variables') {
      steps {
        sh 'echo "=== Jenkins Environment Variables ==="'
        sh 'echo "JOB_NAME: ${JOB_NAME}"'
        sh 'echo "BUILD_NUMBER: ${BUILD_NUMBER}"'
        sh 'echo "WORKSPACE: ${WORKSPACE}"'
        sh 'echo "NODE_NAME: ${NODE_NAME}"'
        sh 'echo "JAVA_HOME: ${JAVA_HOME}"'
      }
    }
    stage('Simulate Work') {
      steps {
        script {
          def sleepTime = Math.floor(Math.random() * 240) + 60 // Random between 60-300 seconds (1-5 minutes)
          echo "Simulating work... sleeping for ${sleepTime} seconds"
          sleep sleepTime
          echo "Work simulation completed!"
        }
      }
    }
  }
  post {
    always {
      echo 'System info pipeline completed'
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
