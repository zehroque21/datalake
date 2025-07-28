#!/bin/bash

# Airflow 2.8.1 MINIMAL Installation Script - ULTRA CLEAN VERSION
# This script installs ONLY Airflow core without ANY providers

# Log all output for debugging
exec > >(tee /var/log/airflow-install.log) 2>&1
echo "$(date): Starting MINIMAL Airflow 2.8.1 installation (NO PROVIDERS)"

# Function to log with timestamp
log() {
    echo "$(date): $1"
}

log "=== MINIMAL AIRFLOW 2.8.1 INSTALLATION STARTING ==="

# Update system (minimal)
log "Updating system packages"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl

# Create airflow user
log "Creating airflow user"
useradd -m -s /bin/bash airflow || log "User airflow may already exist"

# Install Airflow as airflow user
log "Starting MINIMAL Airflow installation as airflow user"
sudo -u airflow bash << 'AIRFLOW_INSTALL'
cd /home/airflow

echo "$(date): Creating Python virtual environment"
python3 -m venv airflow-env
source airflow-env/bin/activate

echo "$(date): Setting up environment variables"
export AIRFLOW_HOME=/home/airflow/airflow

echo "$(date): Upgrading pip"
pip install --upgrade pip

echo "$(date): REMOVING ALL EXISTING AIRFLOW PACKAGES"
pip uninstall -y apache-airflow apache-airflow-core $(pip list | grep apache-airflow | cut -d' ' -f1) || true

echo "$(date): Installing ONLY Airflow core 2.8.1 (NO DEPENDENCIES)"
pip install --no-cache-dir --no-deps "apache-airflow==2.8.1"

echo "$(date): Installing MINIMAL dependencies manually (NO PROVIDERS)"
pip install --no-cache-dir \
    "sqlalchemy>=1.4.28,<2.0" \
    "flask>=2.2,<2.3" \
    "jinja2>=3.0.0" \
    "werkzeug>=2.2,<2.3" \
    "click>=8.0" \
    "python-dateutil>=2.3" \
    "pendulum>=2.1.2,<4.0" \
    "croniter>=0.3.17" \
    "psutil>=4.2.0" \
    "tabulate>=0.7.5" \
    "packaging>=14.0" \
    "markupsafe>=1.1.1" \
    "itsdangerous>=2.0" \
    "blinker" \
    "colorlog>=4.0.2,<5.0"

echo "$(date): Verifying Airflow installation"
INSTALLED_VERSION=$(python3 -c "import airflow; print(airflow.__version__)")
if [[ "$INSTALLED_VERSION" != "2.8.1" ]]; then
    echo "$(date): ERROR: Wrong Airflow version: $INSTALLED_VERSION"
    exit 1
fi

echo "$(date): Creating Airflow directories"
mkdir -p $AIRFLOW_HOME/dags
mkdir -p $AIRFLOW_HOME/logs  
mkdir -p $AIRFLOW_HOME/plugins

echo "$(date): Creating MINIMAL Airflow configuration (NO PROVIDERS)"
cat > $AIRFLOW_HOME/airflow.cfg << 'AIRFLOW_CFG'
[core]
dags_folder = /home/airflow/airflow/dags
base_log_folder = /home/airflow/airflow/logs
plugins_folder = /home/airflow/airflow/plugins
executor = SequentialExecutor
sql_alchemy_conn = sqlite:////home/airflow/airflow/airflow.db
load_examples = False

[webserver]
web_server_host = 0.0.0.0
web_server_port = 8080
authenticate = False

[scheduler]
catchup_by_default = False

[logging]
logging_level = INFO
AIRFLOW_CFG

chmod 600 $AIRFLOW_HOME/airflow.cfg

echo "$(date): Initializing Airflow database (MINIMAL)"
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

echo "$(date): MINIMAL Airflow installation completed successfully"
echo "$(date): Airflow version: $(airflow version)"
AIRFLOW_INSTALL

# Verify Airflow installation was successful
log "Verifying MINIMAL Airflow installation"
if ! sudo -u airflow bash -c "cd /home/airflow && source airflow-env/bin/activate && command -v airflow"; then
    log "ERROR: Airflow installation verification failed"
    exit 1
fi

log "=== MINIMAL AIRFLOW INSTALLATION COMPLETED SUCCESSFULLY ==="
log "Airflow web interface will be available at: http://localhost:8080"
log "Username: admin"
log "Password: admin123"

# Start services directly (no systemd)
log "Starting Airflow webserver in background"
sudo -u airflow bash -c "
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
nohup airflow webserver --port 8080 > /home/airflow/airflow-webserver.log 2>&1 &
echo \$! > /home/airflow/airflow-webserver.pid
"

log "Starting Airflow scheduler in background"
sudo -u airflow bash -c "
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
nohup airflow scheduler > /home/airflow/airflow-scheduler.log 2>&1 &
echo \$! > /home/airflow/airflow-scheduler.pid
"

# Wait for services to start
log "Waiting for services to start"
sleep 20

# Test Airflow web interface
log "Testing Airflow web interface"
for i in {1..10}; do
    if curl -s http://localhost:8080/ > /dev/null; then
        log "SUCCESS: Airflow web interface is responding"
        log "=== MINIMAL AIRFLOW READY FOR USE ==="
        exit 0
    else
        log "Attempt $i: Airflow web interface not ready, waiting..."
        sleep 10
    fi
done

log "ERROR: Airflow failed to respond after 10 attempts"
log "Check logs: /home/airflow/airflow-webserver.log and /home/airflow/airflow-scheduler.log"
exit 1

