pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Start Container') {
            steps {
                sh '''
                    docker compose down || true
                    docker compose up -d --build web
                '''
            }
        }

        stage('Run Django Tests in Container') {
            steps {
                sh '''
                    docker exec inventario_dev bash -lc "
                      export DJANGO_SETTINGS_MODULE=inventario_hospitalario.settings_test
                      python -m pip install --no-cache-dir unittest-xml-reporting
                      rm -rf /app/test-results && mkdir -p /app/test-results
                      python manage.py test inventario.tests \
                        --verbosity 2 \
                        --testrunner=xmlrunner.extra.djangotestrunner.XMLTestRunner \
                        --output-file=/app/test-results
                    "
                    rm -rf test-results
                    docker cp inventario_dev:/app/test-results ./test-results
                '''
            }
        }
    }

    post {
        always {
            junit testResults: 'test-results/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'test-results/*.xml', allowEmptyArchive: true
            sh 'docker compose down || true'
        }
    }
}
