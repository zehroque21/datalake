terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
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

# Security Group for Airflow VM - Restrictive by default
resource "aws_security_group" "airflow_sg" {
  name        = "airflow-security-group"
  description = "Restrictive security group for Airflow VM - No SSH access"
  vpc_id      = data.aws_vpc.default.id

  # Allow outbound internet access for package installation and updates
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP outbound for package installation"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound for package installation"
  }

  # Allow DNS resolution
  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "DNS resolution"
  }

  # Allow Airflow web UI access (only if needed - commented out by default)
  # ingress {
  #   from_port   = 8080
  #   to_port     = 8080
  #   protocol    = "tcp"
  #   cidr_blocks = ["YOUR_IP/32"]  # Replace with your specific IP
  #   description = "Airflow web UI access"
  # }

  # NO SSH ACCESS - Security best practice
  # SSH access should be managed through AWS Systems Manager Session Manager

  tags = {
    Name        = "airflow-security-group"
    Environment = "production"
    Purpose     = "data-engineering"
  }
}

# IAM Role for EC2 instance to access S3 and Systems Manager
resource "aws_iam_role" "airflow_ec2_role" {
  name = "airflow-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "airflow-ec2-role"
    Environment = "production"
    Purpose     = "data-engineering"
  }
}

# IAM Policy for S3 access (least privilege)
resource "aws_iam_policy" "airflow_s3_policy" {
  name        = "airflow-s3-access"
  description = "Policy for Airflow to access specific S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.datalake.arn,
          "${data.aws_s3_bucket.datalake.arn}/*"
        ]
      }
    ]
  })
}

# Attach S3 policy to role
resource "aws_iam_role_policy_attachment" "airflow_s3_attach" {
  role       = aws_iam_role.airflow_ec2_role.name
  policy_arn = aws_iam_policy.airflow_s3_policy.arn
}

# Attach AWS managed policy for Systems Manager (for secure access)
resource "aws_iam_role_policy_attachment" "airflow_ssm_attach" {
  role       = aws_iam_role.airflow_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "airflow_profile" {
  name = "airflow-instance-profile"
  role = aws_iam_role.airflow_ec2_role.name
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
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.airflow_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.airflow_profile.name
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

  # User data for initial setup (secure)
  user_data = base64encode(<<-EOF
    #!/bin/bash
    
    # Update system
    apt-get update -y
    apt-get upgrade -y
    
    # Install essential packages
    apt-get install -y \
      python3 \
      python3-pip \
      python3-venv \
      awscli \
      unzip \
      curl \
      wget
    
    # Install AWS CLI v2
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
    
    # Install Systems Manager Agent (usually pre-installed on Ubuntu)
    snap install amazon-ssm-agent --classic
    systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
    systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
    
    # Create airflow user
    useradd -m -s /bin/bash airflow
    usermod -aG sudo airflow
    
    # Set up Python virtual environment for airflow user
    sudo -u airflow python3 -m venv /home/airflow/airflow-env
    
    # Configure automatic security updates
    apt-get install -y unattended-upgrades
    echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
    
    # Disable unnecessary services
    systemctl disable apache2 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    
    # Set up basic firewall (ufw)
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    
    # Log setup completion
    echo "$(date): Airflow VM setup completed" >> /var/log/setup.log
  EOF
  )

  tags = {
    Name        = "Airflow VM"
    Environment = "production"
    Purpose     = "data-engineering"
    Security    = "hardened"
  }
}

# S3 Bucket reference (existing bucket)
data "aws_s3_bucket" "datalake" {
  bucket = "datalake-bucket-for-airflow-and-delta-v2"
}

# CloudWatch Log Group for monitoring
resource "aws_cloudwatch_log_group" "airflow_logs" {
  name              = "/aws/ec2/airflow"
  retention_in_days = 30

  tags = {
    Name        = "airflow-logs"
    Environment = "production"
    Purpose     = "data-engineering"
  }
}

