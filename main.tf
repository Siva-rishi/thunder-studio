terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.65.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. VPC Setup
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "thunder-studio-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true
}

# 2. Security Group for RDS
resource "aws_security_group" "db_sg" {
  name        = "thunder-studio-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. DB Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "thunder-studio-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# 4. RDS MySQL Instance
resource "aws_db_instance" "rds_mysql" {
  allocated_storage      = 20
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  db_name                = "thunderstudio"
  username               = "admin"
  password               = "ThunderSecurePass123!"
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
}

# 5. ECR Repository
resource "aws_ecr_repository" "app_repo" {
  name                 = "thunder-studio-backend"
  image_tag_mutability = "MUTABLE"
}
