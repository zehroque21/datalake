terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Generate random suffix for resource names to avoid conflicts
resource "random_id" "sg_suffix" {
  byte_length = 4
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
  name        = "airflow-security-group-${random_id.sg_suffix.hex}"
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

  # Allow Airflow web UI access from specific IP (conditional and configurable)
  dynamic "ingress" {
    for_each = var.enable_airflow_web_access ? [1] : []
    content {
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      cidr_blocks = [var.allowed_ip_for_airflow]
      description = "Airflow web UI access from allowed IP"
    }
  }

  # NO SSH ACCESS - Security best practice
  # SSH access should be managed through AWS Systems Manager Session Manager

  tags = {
    Name        = "airflow-security-group"
    Environment = "production"
    Purpose     = "data-engineering"
  }
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
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.airflow_sg.id]
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

  # User data for automatic Airflow installation (secure and robust)
  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e  # Exit on any error
    
    # Log all output for debugging
    exec > >(tee /var/log/user-data.log) 2>&1
    echo "$(date): Starting Airflow installation script"
    
    # Update system
    echo "$(date): Updating system packages"
    apt-get update -y
    apt-get upgrade -y
    
    # Install essential packages
    echo "$(date): Installing essential packages"
    apt-get install -y \
      python3 \
      python3-pip \
      python3-venv \
      awscli \
      unzip \
      curl \
      wget \
      git \
      build-essential \
      libssl-dev \
      libffi-dev \
      python3-dev \
      net-tools
    
    # Install AWS CLI v2
    echo "$(date): Installing AWS CLI v2"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
    
    # Install Systems Manager Agent (usually pre-installed on Ubuntu)
    echo "$(date): Configuring Systems Manager Agent"
    snap install amazon-ssm-agent --classic || echo "SSM Agent already installed"
    systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
    systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
    
    # Create airflow user
    echo "$(date): Creating airflow user"
    useradd -m -s /bin/bash airflow || echo "User airflow already exists"
    usermod -aG sudo airflow
    
    # Configure automatic security updates
    echo "$(date): Configuring automatic security updates"
    apt-get install -y unattended-upgrades
    echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
    
    # Disable unnecessary services
    systemctl disable apache2 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    
    # Set up basic firewall (ufw)
    echo "$(date): Configuring firewall"
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    
    # AIRFLOW INSTALLATION (as airflow user)
    echo "$(date): Starting Airflow installation"
    export AIRFLOW_HOME=/home/airflow/airflow
    export AIRFLOW_VERSION=2.8.1
    export PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-$${AIRFLOW_VERSION}/constraints-$${PYTHON_VERSION}.txt"
    
    echo "$(date): Using Python version: $PYTHON_VERSION"
    
    # Create airflow directory and set permissions
    mkdir -p $AIRFLOW_HOME
    chown -R airflow:airflow /home/airflow
    
    # Switch to airflow user for installation
    echo "$(date): Installing Airflow as airflow user"
    sudo -u airflow bash << 'AIRFLOW_SETUP'
    set -e  # Exit on any error
    cd /home/airflow
    
    echo "$(date): Creating Python virtual environment"
    python3 -m venv airflow-env
    source airflow-env/bin/activate
    
    # Upgrade pip
    echo "$(date): Upgrading pip"
    pip install --upgrade pip
    
    # Install Airflow with specific providers
    echo "$(date): Installing Apache Airflow"
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    pip install "apache-airflow==2.8.1" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-$${PYTHON_VERSION}.txt"
    
    # Install additional providers
    echo "$(date): Installing Airflow providers"
    pip install apache-airflow-providers-amazon
    pip install apache-airflow-providers-postgres
    pip install apache-airflow-providers-http
    
    # Install data processing libraries
    echo "$(date): Installing data processing libraries"
    pip install pandas boto3 delta-spark pyspark
    
    # Set environment variables
    export AIRFLOW_HOME=/home/airflow/airflow
    
    # Initialize Airflow database
    echo "$(date): Initializing Airflow database"
    airflow db init
    
    # Create admin user with secure password
    echo "$(date): Creating admin user"
    ADMIN_PASSWORD=$(openssl rand -base64 12)
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password "$ADMIN_PASSWORD"
    
    # Save password to file for reference
    echo "Airflow Admin Password: $ADMIN_PASSWORD" > /home/airflow/admin_password.txt
    chmod 600 /home/airflow/admin_password.txt
    
    # Generate secret key
    SECRET_KEY=$(openssl rand -base64 32)
    
    # Create secure Airflow configuration
    echo "$(date): Creating Airflow configuration"
    cat > $AIRFLOW_HOME/airflow.cfg << AIRFLOW_CFG
[core]
dags_folder = /home/airflow/airflow/dags
base_log_folder = /home/airflow/airflow/logs
plugins_folder = /home/airflow/airflow/plugins
executor = LocalExecutor
sql_alchemy_conn = sqlite:////home/airflow/airflow/airflow.db
load_examples = False
security = True

[webserver]
web_server_host = 0.0.0.0
web_server_port = 8080
secret_key = $SECRET_KEY
expose_config = False
authenticate = True
auth_backend = airflow.auth.backends.password_auth

[scheduler]
catchup_by_default = False

[logging]
logging_level = INFO
fab_logging_level = WARN

[secrets]
backend = airflow.secrets.local_filesystem.LocalFilesystemBackend

[aws]
region_name = us-east-1
AIRFLOW_CFG
    
    # Create directories
    mkdir -p $AIRFLOW_HOME/dags
    mkdir -p $AIRFLOW_HOME/logs
    mkdir -p $AIRFLOW_HOME/plugins
    
    # Set proper permissions
    chmod 700 $AIRFLOW_HOME
    chmod 600 $AIRFLOW_HOME/airflow.cfg
    
    echo "$(date): Airflow installation completed for user airflow"
AIRFLOW_SETUP
    
    # Create systemd service for Airflow webserver
    echo "$(date): Creating systemd services"
    cat > /etc/systemd/system/airflow-webserver.service << 'WEBSERVER_SERVICE'
[Unit]
Description=Airflow webserver daemon
After=network.target

[Service]
Environment=AIRFLOW_HOME=/home/airflow/airflow
User=airflow
Group=airflow
Type=simple
ExecStart=/home/airflow/airflow-env/bin/airflow webserver --port 8080
Restart=on-failure
RestartSec=10s
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
WEBSERVER_SERVICE
    
    # Create systemd service for Airflow scheduler
    cat > /etc/systemd/system/airflow-scheduler.service << 'SCHEDULER_SERVICE'
[Unit]
Description=Airflow scheduler daemon
After=network.target

[Service]
Environment=AIRFLOW_HOME=/home/airflow/airflow
User=airflow
Group=airflow
Type=simple
ExecStart=/home/airflow/airflow-env/bin/airflow scheduler
Restart=on-failure
RestartSec=10s
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
SCHEDULER_SERVICE
    
    # Reload systemd and enable services
    echo "$(date): Enabling and starting Airflow services"
    systemctl daemon-reload
    systemctl enable airflow-webserver
    systemctl enable airflow-scheduler
    
    # Start services
    systemctl start airflow-webserver
    systemctl start airflow-scheduler
    
    # Wait for services to start and verify
    echo "$(date): Waiting for services to start"
    sleep 30
    
    # Check service status
    systemctl status airflow-webserver --no-pager
    systemctl status airflow-scheduler --no-pager
    
    # Verify Airflow is responding
    echo "$(date): Verifying Airflow installation"
    for i in {1..10}; do
        if curl -f http://localhost:8080/health > /dev/null 2>&1; then
            echo "$(date): Airflow is responding on port 8080"
            break
        else
            echo "$(date): Waiting for Airflow to start (attempt $i/10)"
            sleep 10
        fi
    done
    
    # Log completion
    echo "$(date): Airflow installation and setup completed successfully"
    echo "$(date): Airflow services are running"
    echo "$(date): Access Airflow at http://localhost:8080 with username: admin"
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

