pipeline {
    agent any
    environment {
        AWS_ACCOUNT_ID = '182719847108'
        AWS_REGION     = 'us-east-1'
        ECR_REPO       = 'thunder-studio-backend'
        IMAGE_TAG      = "${BUILD_NUMBER}"
    }
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/Siva-rishi/thunder-studio.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${ECR_REPO}:${IMAGE_TAG} ."
            }
        }
        stage('Push Image to AWS ECR') {
            steps {
                sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                sh "docker tag ${ECR_REPO}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"
                sh "docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"
            }
        }
        stage('Deploy to Kubernetes (EKS)') {
            steps {
                sh "aws eks update-kubeconfig --region ${AWS_REGION} --name thunder-studio-eks"
                sh "kubectl set image deployment/thunder-studio-backend backend=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"
            }
        }
    }
}
