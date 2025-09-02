NAME = 'parallel_pipeline'
DSL = '''pipeline {
  agent any
  stages {
    stage('Parallel Execution') {
      parallel {
        stage('Branch A') {
          steps {
            echo 'Executing Branch A'
            sh 'echo "Branch A started at $(date)" > branch_a.log'
            sh 'sleep 2'
            sh 'echo "Branch A completed at $(date)" >> branch_a.log'
            sh 'cat branch_a.log'
          }
        }
        stage('Branch B') {
          steps {
            echo 'Executing Branch B'
            sh 'echo "Branch B started at $(date)" > branch_b.log'
            sh 'sleep 3'
            sh 'echo "Branch B completed at $(date)" >> branch_b.log'
            sh 'cat branch_b.log'
          }
        }
        stage('Branch C') {
          steps {
            echo 'Executing Branch C'
            sh 'echo "Branch C started at $(date)" > branch_c.log'
            sh 'sleep 1'
            sh 'echo "Branch C completed at $(date)" >> branch_c.log'
            sh 'cat branch_c.log'
          }
        }
      }
    }
    stage('Merge Results') {
      steps {
        echo 'Merging results from parallel branches'
        sh 'echo "=== Parallel Execution Results ===" > results.log'
        sh 'cat branch_a.log >> results.log'
        sh 'cat branch_b.log >> results.log'
        sh 'cat branch_c.log >> results.log'
        sh 'echo "=== End Results ===" >> results.log'
        sh 'cat results.log'
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: '*.log', allowEmptyArchive: true
      sh 'rm -f *.log'
    }
    success {
      echo 'Parallel pipeline completed successfully!'
    }
    failure {
      echo 'Parallel pipeline failed!'
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
