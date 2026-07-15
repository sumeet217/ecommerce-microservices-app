pipeline {

    agent any

    environment {
        DOCKER_HUB_USER  = "sumeet02"
        DOCKER_HUB_CREDS = credentials("docker-hub-creds")
        NVD_API_KEY      = credentials("nvd-api-key")

        AUTH_IMAGE    = "${DOCKER_HUB_USER}/django-auth-service"
        CATALOG_IMAGE = "${DOCKER_HUB_USER}/django-retail-catalog"
        CART_IMAGE    = "${DOCKER_HUB_USER}/django-retail-cart"
        ORDERS_IMAGE  = "${DOCKER_HUB_USER}/django-retail-orders"
        UI_IMAGE      = "${DOCKER_HUB_USER}/django-retail-ui"

        IMAGE_TAG    = "v${BUILD_NUMBER}"
        SONAR_SCANNER = tool('sonar-scanner')
    }

    stages {

        stage("Clone Code") {
            steps {
                echo "Cloning code from GitHub"
                git url: "https://github.com/sumeet217/ecommerce-microservices-app.git", branch: "main"
            }
        }

        stage("Setup .env File") {
            steps {
                echo "Setting up .env file"
                withCredentials([file(credentialsId: "app-env-file", variable: "ENV_FILE")]) {
                    sh "cp \$ENV_FILE .env"
                }
                echo ".env file is ready!"
            }
        }

        stage('SonarQube Quality Analysis') {
            steps {
                withSonarQubeEnv('sonar') {
                    sh "${SONAR_SCANNER}/bin/sonar-scanner -Dsonar.projectName=retail-store -Dsonar.projectKey=retail-store"
                }
            }
        }

        stage('Sonar Quality Gate') {
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        stage('OWASP Dependency Check') {
            steps {
                dependencyCheck additionalArguments: "--scan ./ --format XML --nvdApiKey ${NVD_API_KEY}", odcInstallation: 'owaspDC'
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
            }
        }

        stage('Trivy File System Scan') {
            steps {
                sh "trivy fs --severity HIGH,CRITICAL --format table -o trivy-fs-report.txt ."
            }
        }

        stage("Build Docker Images") {
            steps {
                echo "Building Docker Images"
                sh "docker build -t ${AUTH_IMAGE}:${IMAGE_TAG}    ./retail-store/services/auth/"
                sh "docker build -t ${CATALOG_IMAGE}:${IMAGE_TAG} ./retail-store/services/catalog/"
                sh "docker build -t ${CART_IMAGE}:${IMAGE_TAG}    ./retail-store/services/cart/"
                sh "docker build -t ${ORDERS_IMAGE}:${IMAGE_TAG}  ./retail-store/services/orders/"
                sh "docker build -t ${UI_IMAGE}:${IMAGE_TAG}      ./retail-store/services/ui/"
                echo "All 5 images built successfully!"
            }
        }

        stage("Push to Docker Hub") {
            steps {
                echo "Pushing Images to Docker Hub"
                sh "echo ${DOCKER_HUB_CREDS_PSW} | docker login -u ${DOCKER_HUB_CREDS_USR} --password-stdin"
                sh "docker push ${AUTH_IMAGE}:${IMAGE_TAG}"
                sh "docker push ${CATALOG_IMAGE}:${IMAGE_TAG}"
                sh "docker push ${CART_IMAGE}:${IMAGE_TAG}"
                sh "docker push ${ORDERS_IMAGE}:${IMAGE_TAG}"
                sh "docker push ${UI_IMAGE}:${IMAGE_TAG}"
                echo "All images pushed to Docker Hub!"
            }
        }

        stage('Trivy Image Scan') {
            steps {
                script {
                    def images = [
                        'django-auth-service',
                        'django-retail-catalog',
                        'django-retail-cart',
                        'django-retail-orders',
                        'django-retail-ui'
                    ]
                    images.each { img ->
                        sh "trivy image --severity HIGH,CRITICAL --format table -o trivy-${img}-report.txt ${DOCKER_HUB_USER}/${img}:${IMAGE_TAG}"
                    }
                }
            }
        }

        stage("Deploy") {
            steps {
                echo "Deploying on EC2"
                sh """
                    IMAGE_TAG=${IMAGE_TAG} docker-compose -f docker-compose.prod.yml pull
                    IMAGE_TAG=${IMAGE_TAG} docker-compose -f docker-compose.prod.yml up -d --remove-orphans
                    docker image prune -f
                """
                echo "Deployment done! All services are up and running."
            }
        }

        stage("Cleanup") {
            steps {
                echo "Cleaning up local Docker images"
                sh """
                    docker rmi -f ${AUTH_IMAGE}:${IMAGE_TAG}
                    docker rmi -f ${CATALOG_IMAGE}:${IMAGE_TAG}
                    docker rmi -f ${CART_IMAGE}:${IMAGE_TAG}
                    docker rmi -f ${ORDERS_IMAGE}:${IMAGE_TAG}
                    docker rmi -f ${UI_IMAGE}:${IMAGE_TAG}
                    docker image prune -f
                    docker builder prune -f
                """
                echo "Cleanup done!"
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCEEDED! Build #${BUILD_NUMBER} is now live."
        }
        failure {
            echo "Pipeline FAILED! Scroll up in the logs to find the error."
        }
        always {
            sh "docker logout"
            sh "rm -f .env"
            cleanWs()
        }
    }
}