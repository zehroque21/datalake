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
pip install --upgrade pip || { echo "$(date): ERROR: Failed to upgrade pip"; exit 1; }

echo "$(date): Installing Apache Airflow"
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "$(date): Using Python version: $PYTHON_VERSION"

# Install Airflow with explicit version pinning and no-deps to avoid conflicts
echo "$(date): Installing Airflow 2.8.1 with strict version control"
pip install --no-deps "apache-airflow==2.8.1" || {
    echo "$(date): ERROR: Failed to install Apache Airflow core"
    exit 1
}

# Install dependencies with constraints
echo "$(date): Installing Airflow dependencies with constraints"
pip install --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-$${PYTHON_VERSION}.txt" \
    "apache-airflow[celery,postgres,mysql,redis]==2.8.1" || {
    echo "$(date): ERROR: Failed to install Airflow dependencies"
    exit 1
}

# Verify Airflow installation
echo "$(date): Verifying Airflow installation"
if ! command -v airflow &> /dev/null; then
    echo "$(date): ERROR: Airflow command not found after installation"
    exit 1
fi

# Test Airflow version
echo "$(date): Testing Airflow installation"
airflow version || {
    echo "$(date): ERROR: Airflow version command failed"
    exit 1
}

echo "$(date): Installing Airflow providers"
pip install apache-airflow-providers-amazon || {
    echo "$(date): WARNING: Failed to install AWS provider"
}
pip install pandas boto3 || {
    echo "$(date): WARNING: Failed to install pandas/boto3"
}

echo "$(date): Creating Airflow directories"
mkdir -p $AIRFLOW_HOME/dags
mkdir -p $AIRFLOW_HOME/logs  
mkdir -p $AIRFLOW_HOME/plugins

echo "$(date): Initializing Airflow database"
airflow db init || {
    echo "$(date): ERROR: Failed to initialize Airflow database"
    exit 1
}

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

# Final verification that everything is working
echo "$(date): Performing final verification"
airflow version || {
    echo "$(date): ERROR: Final Airflow verification failed"
    exit 1
}

# Test that Airflow can access its configuration
airflow config list --defaults > /dev/null || {
    echo "$(date): ERROR: Airflow configuration test failed"
    exit 1
}

echo "$(date): Airflow installation completed successfully"
echo "$(date): Airflow version: $(airflow version)"
AIRFLOW_INSTALL

# Verify Airflow installation was successful before creating services
log "Verifying Airflow installation before creating services"
if ! sudo -u airflow bash -c "cd /home/airflow && source airflow-env/bin/activate && command -v airflow"; then
    log "ERROR: Airflow installation verification failed"
    exit 1
fi

# Create startup scripts for systemd (outside of airflow user context)
log "Creating startup scripts for systemd"
cat > /home/airflow/start-webserver.sh << 'WEBSERVER_SCRIPT'
#!/bin/bash
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
exec airflow webserver --port 8080
WEBSERVER_SCRIPT

cat > /home/airflow/start-scheduler.sh << 'SCHEDULER_SCRIPT'
#!/bin/bash
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
exec airflow scheduler
SCHEDULER_SCRIPT

# Set proper ownership and permissions
log "Setting script permissions and ownership"
run_cmd "chown airflow:airflow /home/airflow/start-webserver.sh"
run_cmd "chown airflow:airflow /home/airflow/start-scheduler.sh"
run_cmd "chmod +x /home/airflow/start-webserver.sh"
run_cmd "chmod +x /home/airflow/start-scheduler.sh"

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

# Enhanced final verification
log "Performing enhanced Airflow verification"
VERIFICATION_FAILED=false

# Check if services are active
if ! systemctl is-active --quiet airflow-webserver; then
    log "ERROR: Airflow webserver service is not active"
    VERIFICATION_FAILED=true
fi

if ! systemctl is-active --quiet airflow-scheduler; then
    log "ERROR: Airflow scheduler service is not active"
    VERIFICATION_FAILED=true
fi

# Check if Airflow is responding on port 8080
log "Testing Airflow web interface"
for i in {1..15}; do
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log "SUCCESS: Airflow is responding on port 8080"
        break
    else
        log "Attempt $i/15: Waiting for Airflow to respond"
        if [ $i -eq 15 ]; then
            log "ERROR: Airflow failed to respond after 15 attempts"
            VERIFICATION_FAILED=true
        fi
        sleep 10
    fi
done

# Final status report
if [ "$VERIFICATION_FAILED" = true ]; then
    log "=== AIRFLOW INSTALLATION FAILED ==="
    log "Some verification checks failed. Check logs above for details."
    log "Manual troubleshooting may be required."
    exit 1
else
    log "=== AIRFLOW INSTALLATION COMPLETED SUCCESSFULLY ==="
    log "All verification checks passed!"
    log "Access Airflow at http://localhost:8080"
    log "Username: admin | Password: admin123"
    log "Credentials saved in: /home/airflow/admin_credentials.txt"
    log "Use AWS Session Manager for secure access"
fi

# Configure auto-stop for cost management
log "Configuring auto-stop for cost management"

# Install AWS CLI v2 if not already installed (for auto-stop functionality)
if ! command -v aws &> /dev/null; then
    log "Installing AWS CLI v2 for auto-stop functionality"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
fi

# Create auto-stop script
log "Creating auto-stop script"
cat > /usr/local/bin/auto-stop-instance.sh << 'AUTO_STOP_SCRIPT'
#!/bin/bash
# Auto-stop script for cost management
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

echo "$(date): Auto-stop triggered for instance $INSTANCE_ID in region $REGION"

# Stop the instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION

echo "$(date): Stop command sent for instance $INSTANCE_ID"
AUTO_STOP_SCRIPT

chmod +x /usr/local/bin/auto-stop-instance.sh

# Configure cron job for auto-stop at 22:00 (10 PM) daily
log "Configuring daily auto-stop at 22:00 (10 PM)"
echo "0 22 * * * /usr/local/bin/auto-stop-instance.sh >> /var/log/auto-stop.log 2>&1" | crontab -

# Create manual stop script for immediate use
log "Creating manual stop script"
cat > /usr/local/bin/stop-now.sh << 'STOP_NOW_SCRIPT'
#!/bin/bash
echo "Stopping instance immediately..."
/usr/local/bin/auto-stop-instance.sh
STOP_NOW_SCRIPT

chmod +x /usr/local/bin/stop-now.sh

log "=== AUTO-STOP CONFIGURATION COMPLETED ==="
log "Instance will automatically stop at 22:00 (10 PM) daily"
log "To stop manually: sudo /usr/local/bin/stop-now.sh"
log "To check auto-stop logs: sudo tail -f /var/log/auto-stop.log"
log "To disable auto-stop: sudo crontab -r"

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
  bucket = var.bucket_name
}

