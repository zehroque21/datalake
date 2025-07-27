terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security Group for Airflow VM - Reference existing
data "aws_security_group" "airflow_sg" {
  name = "airflow-security-group-stable"
}

# IAM Role for EC2 instance (reference existing role)
data "aws_iam_role" "airflow_ec2_role" {
  name = "airflow-ec2-role"
}

# IAM Policy for S3 access (reference existing policy)
data "aws_iam_policy" "airflow_s3_policy" {
  name = "airflow-s3-access"
}

# IAM Instance Profile (reference existing profile)
data "aws_iam_instance_profile" "airflow_profile" {
  name = "airflow-instance-profile"
}

# Get latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}

# EC2 Instance with security improvements
resource "aws_instance" "airflow_vm" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [data.aws_security_group.airflow_sg.id]
  iam_instance_profile   = data.aws_iam_instance_profile.airflow_profile.name
  subnet_id              = data.aws_subnets.default.ids[0]

  # Security configurations
  monitoring                           = true
  disable_api_termination              = false
  instance_initiated_shutdown_behavior = "stop"

  # No key pair - access via Systems Manager Session Manager only
  # key_name = null  # Explicitly no SSH key

  # EBS encryption
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name        = "airflow-root-volume"
      Environment = "production"
      Purpose     = "data-engineering"
    }
  }

  # IMDSv2 configuration for enhanced security
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # Force IMDSv2
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  # User data for automatic Airflow installation (using external script)
  user_data = base64encode(templatefile("${path.module}/../scripts/install_airflow_v2.sh", {}))

  tags = {
    Name        = "Airflow VM"
    Environment = "production"
    Purpose     = "data-engineering"
    Security    = "hardened"
  }
}

# S3 Bucket reference (existing bucket)
data "aws_s3_bucket" "datalake" {
  bucket = var.bucket_name
}

