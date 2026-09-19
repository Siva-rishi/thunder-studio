pipeline {
    agent any

    environment {
        AWS_REGION     = 'us-east-1'
        ECR_REPO_NAME  = 'thunder-studio-backend'
        AWS_ACCOUNT_ID = '182719847108'
        IMAGE_URI      = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                git branch: 'main', url: 'https://github.com/Siva-rishi/thunder-studio.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_URI}:${BUILD_NUMBER} ."
                    sh "docker tag ${IMAGE_URI}:${BUILD_NUMBER} ${IMAGE_URI}:latest"
                }
            }
        }

        stage('Push Image to AWS ECR') {
            steps {
                script {
                    sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                    sh "docker push ${IMAGE_URI}:${BUILD_NUMBER}"
                    sh "docker push ${IMAGE_URI}:latest"
                }
            }
        }

        stage('Deploy to (EKS)') {
            steps {
                script {
                    sh "aws eks update-kubeconfig --region ${AWS_REGION} --name thunder-studio-eks"
                    sh "kubectl apply -f k8s/secret.yaml"
                    sh "kubectl apply -f k8s/deployment.yaml"
                    sh "kubectl apply -f k8s/service.yaml"
                    sh "kubectl set image deployment/thunder-backend-deployment flask-app=${IMAGE_URI}:${BUILD_NUMBER}"
                }
            }
        }
    }

    post {
        always {
            sh "docker logout ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
            cleanWs()
        }
    }
}
