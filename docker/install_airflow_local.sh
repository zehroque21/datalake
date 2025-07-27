#!/bin/bash

# Airflow 2.8.1 Installation Script - LOCAL TESTING VERSION
# This script is for Docker testing only - includes fix for provider compatibility

# Log all output for debugging
exec > >(tee /var/log/airflow-install.log) 2>&1
echo "$(date): Starting Airflow 2.8.1 installation script (LOCAL VERSION)"

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

log "=== AIRFLOW 2.8.1 INSTALLATION STARTING ==="

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

echo "$(date): Installing Apache Airflow 2.8.1 with robust version control"
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "$(date): Using Python version: $PYTHON_VERSION"

# Clear any existing airflow installations
pip uninstall apache-airflow apache-airflow-core -y || true

# Install specific version with working constraint file (using 3.11 constraints that work)
echo "$(date): Installing Airflow 2.8.1 with working constraint file"
pip install --no-cache-dir \
    "apache-airflow==2.8.1" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.11.txt" \
    --force-reinstall || {
    echo "$(date): ERROR: Failed to install Apache Airflow 2.8.1"
    exit 1
}

# Verify specific version was installed
echo "$(date): Verifying Airflow 2.8.1 installation"
INSTALLED_VERSION=$(pip show apache-airflow | grep Version | cut -d' ' -f2)
if [[ "$INSTALLED_VERSION" != "2.8.1" ]]; then
    echo "$(date): ERROR: Wrong Airflow version installed: $INSTALLED_VERSION (expected 2.8.1)"
    exit 1
fi

# Verify executable exists
if [[ ! -f "/home/airflow/airflow-env/bin/airflow" ]]; then
    echo "$(date): ERROR: Airflow executable not found at expected location"
    exit 1
fi

echo "$(date): Airflow 2.8.1 successfully installed and verified"

# Test Airflow version
echo "$(date): Testing Airflow installation"
airflow version || {
    echo "$(date): ERROR: Airflow version command failed"
    exit 1
}

echo "$(date): Installing only essential packages (no providers to avoid conflicts)"
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

# Verify Airflow installation was successful
log "Verifying Airflow installation"
if ! sudo -u airflow bash -c "cd /home/airflow && source airflow-env/bin/activate && command -v airflow"; then
    log "ERROR: Airflow installation verification failed"
    exit 1
fi

log "=== AIRFLOW INSTALLATION COMPLETED SUCCESSFULLY ==="
log "Airflow web interface will be available at: http://localhost:8080"
log "Username: admin"
log "Password: admin123"

# For Docker, we'll start services manually instead of using systemd
log "Starting Airflow webserver in background"
sudo -u airflow bash -c "
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
nohup airflow webserver --port 8080 > /var/log/airflow-webserver.log 2>&1 &
echo \$! > /var/run/airflow-webserver.pid
"

log "Starting Airflow scheduler in background"
sudo -u airflow bash -c "
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
nohup airflow scheduler > /var/log/airflow-scheduler.log 2>&1 &
echo \$! > /var/run/airflow-scheduler.pid
"

# Wait for services to start
log "Waiting for services to start"
sleep 15

# Test Airflow web interface
log "Testing Airflow web interface"
for i in {1..10}; do
    if curl -s http://localhost:8080/health > /dev/null; then
        log "SUCCESS: Airflow web interface is responding"
        log "=== AIRFLOW READY FOR USE ==="
        exit 0
    else
        log "Attempt $i: Airflow web interface not ready, waiting..."
        sleep 10
    fi
done

log "ERROR: Airflow failed to respond after 10 attempts"
log "Check logs: /var/log/airflow-webserver.log and /var/log/airflow-scheduler.log"
exit 1

