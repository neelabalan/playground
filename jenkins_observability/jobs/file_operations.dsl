NAME = 'file_operations'
DSL = '''pipeline {
  agent any
  stages {
    stage('Create Files') {
      steps {
        sh 'echo "Creating sample files..."'
        sh 'echo "Hello from Jenkins pipeline!" > hello.txt'
        sh 'echo "Build number: ${BUILD_NUMBER}" > build_info.txt'
        sh 'echo "Job name: ${JOB_NAME}" >> build_info.txt'
        sh 'date > timestamp.txt'
        sh 'ls -la *.txt'
      }
    }
    stage('Process Files') {
      steps {
        sh 'echo "Processing files..."'
        sh 'cat hello.txt'
        sh 'cat build_info.txt'
        sh 'echo "File contents:"'
        sh 'for file in *.txt; do echo "=== $file ==="; cat $file; echo ""; done'
      }
    }
    stage('Archive Results') {
      steps {
        sh 'echo "Creating archive..."'
        sh 'tar -czf pipeline_output_${BUILD_NUMBER}.tar.gz *.txt'
        sh 'ls -la *.tar.gz'
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: '*.txt,*.tar.gz', allowEmptyArchive: true
      sh 'echo "Cleaning up..."'
      sh 'rm -f *.txt *.tar.gz'
    }
    success {
      echo 'File operations pipeline completed successfully!'
    }
    failure {
      echo 'File operations pipeline failed!'
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
