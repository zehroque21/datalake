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

  # User data for automatic Airflow installation (fixed and robust)
  user_data = base64encode(<<-EOF
#!/bin/bash

# Log all output for debugging
exec > >(tee /var/log/user-data.log) 2>&1
echo "$(date): Starting Airflow installation script"

# Function to log with timestamp
log() {
    echo "$(date): $1"
}

# Function to run commands with error handling
run_cmd() {
    log "Running: $1"
    if eval "$1"; then
        log "SUCCESS: $1"
        return 0
    else
        log "ERROR: Failed to run: $1"
        return 1
    fi
}

log "=== AIRFLOW INSTALLATION STARTING ==="

# Update system
log "Updating system packages"
run_cmd "apt-get update -y"
run_cmd "apt-get upgrade -y"

# Install essential packages
log "Installing essential packages"
run_cmd "apt-get install -y python3 python3-pip python3-venv build-essential libssl-dev libffi-dev python3-dev net-tools curl wget git"

# Create airflow user
log "Creating airflow user"
run_cmd "useradd -m -s /bin/bash airflow" || log "User airflow may already exist"
run_cmd "usermod -aG sudo airflow"

# Configure firewall
log "Configuring basic firewall"
run_cmd "ufw --force enable"
run_cmd "ufw default deny incoming"
run_cmd "ufw default allow outgoing"

# Install Airflow as airflow user
log "Starting Airflow installation as airflow user"
sudo -u airflow bash << 'AIRFLOW_INSTALL'
cd /home/airflow

echo "$(date): Creating Python virtual environment"
python3 -m venv airflow-env
source airflow-env/bin/activate

echo "$(date): Setting up environment variables"
export AIRFLOW_HOME=/home/airflow/airflow

echo "$(date): Upgrading pip"
pip install --upgrade pip

echo "$(date): Installing Apache Airflow"
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
pip install "apache-airflow==2.8.1" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-$${PYTHON_VERSION}.txt"

echo "$(date): Installing Airflow providers"
pip install apache-airflow-providers-amazon
pip install pandas boto3

echo "$(date): Creating Airflow directories"
mkdir -p $AIRFLOW_HOME/dags
mkdir -p $AIRFLOW_HOME/logs  
mkdir -p $AIRFLOW_HOME/plugins

echo "$(date): Initializing Airflow database"
airflow db init

echo "$(date): Creating admin user"
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin123

echo "$(date): Saving admin credentials"
echo "Username: admin" > /home/airflow/admin_credentials.txt
echo "Password: admin123" >> /home/airflow/admin_credentials.txt
chmod 600 /home/airflow/admin_credentials.txt

echo "$(date): Creating Airflow configuration"
cat > $AIRFLOW_HOME/airflow.cfg << 'AIRFLOW_CFG'
[core]
dags_folder = /home/airflow/airflow/dags
base_log_folder = /home/airflow/airflow/logs
plugins_folder = /home/airflow/airflow/plugins
executor = LocalExecutor
sql_alchemy_conn = sqlite:////home/airflow/airflow/airflow.db
load_examples = False

[webserver]
web_server_host = 0.0.0.0
web_server_port = 8080
authenticate = True
auth_backend = airflow.auth.backends.password_auth

[scheduler]
catchup_by_default = False

[logging]
logging_level = INFO

[aws]
region_name = us-east-1
AIRFLOW_CFG

chmod 600 $AIRFLOW_HOME/airflow.cfg

echo "$(date): Creating startup scripts for systemd"
# Create webserver startup script
cat > /home/airflow/start-webserver.sh << 'WEBSERVER_SCRIPT'
#!/bin/bash
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
exec airflow webserver --port 8080
WEBSERVER_SCRIPT

# Create scheduler startup script
cat > /home/airflow/start-scheduler.sh << 'SCHEDULER_SCRIPT'
#!/bin/bash
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
exec airflow scheduler
SCHEDULER_SCRIPT

chmod +x /home/airflow/start-webserver.sh
chmod +x /home/airflow/start-scheduler.sh

echo "$(date): Airflow installation completed successfully"
AIRFLOW_INSTALL

# Create systemd services with proper environment setup
log "Creating systemd services"
cat > /etc/systemd/system/airflow-webserver.service << 'WEBSERVER_SERVICE'
[Unit]
Description=Airflow webserver daemon
After=network.target

[Service]
Type=simple
User=airflow
Group=airflow
ExecStart=/home/airflow/start-webserver.sh
Restart=on-failure
RestartSec=10s
WorkingDirectory=/home/airflow
Environment=PATH=/home/airflow/airflow-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=AIRFLOW_HOME=/home/airflow/airflow

[Install]
WantedBy=multi-user.target
WEBSERVER_SERVICE

cat > /etc/systemd/system/airflow-scheduler.service << 'SCHEDULER_SERVICE'
[Unit]
Description=Airflow scheduler daemon
After=network.target

[Service]
Type=simple
User=airflow
Group=airflow
ExecStart=/home/airflow/start-scheduler.sh
Restart=on-failure
RestartSec=10s
WorkingDirectory=/home/airflow
Environment=PATH=/home/airflow/airflow-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=AIRFLOW_HOME=/home/airflow/airflow

[Install]
WantedBy=multi-user.target
SCHEDULER_SERVICE

# Enable and start services
log "Enabling and starting Airflow services"
run_cmd "systemctl daemon-reload"
run_cmd "systemctl enable airflow-webserver"
run_cmd "systemctl enable airflow-scheduler"
run_cmd "systemctl start airflow-webserver"
run_cmd "systemctl start airflow-scheduler"

# Wait and verify
log "Waiting for services to start"
sleep 30

log "Checking service status"
systemctl status airflow-webserver --no-pager || log "Webserver status check failed"
systemctl status airflow-scheduler --no-pager || log "Scheduler status check failed"

# Final verification
log "Verifying Airflow installation"
for i in {1..10}; do
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log "SUCCESS: Airflow is responding on port 8080"
        break
    else
        log "Attempt $i/10: Waiting for Airflow to respond"
        sleep 10
    fi
done

log "=== AIRFLOW INSTALLATION COMPLETED ==="
log "Access Airflow at http://localhost:8080"
log "Username: admin | Password: admin123"
log "Credentials saved in: /home/airflow/admin_credentials.txt"

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

