#!/bin/bash

# Airflow 2.8.1 ULTRA-AGGRESSIVE Installation Script for EC2
# This script ensures ONLY Airflow 2.8.1 is installed with extreme cleanup

# Log all output for debugging
exec > >(tee /var/log/airflow-install.log) 2>&1
echo "$(date): Starting ULTRA-AGGRESSIVE Airflow 2.8.1 installation for EC2"

# Function to log with timestamp
log() {
    echo "$(date): $1"
}

# Function to run command with error handling
run_cmd() {
    local cmd="$1"
    log "Running: $cmd"
    if eval "$cmd"; then
        log "SUCCESS: $cmd"
    else
        log "ERROR: Failed to run: $cmd"
        return 1
    fi
}

log "=== ULTRA-AGGRESSIVE AIRFLOW 2.8.1 INSTALLATION STARTING ==="

# Update system packages
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

# Configure basic firewall
log "Configuring basic firewall"
run_cmd "ufw --force enable" || log "UFW may not be available"
run_cmd "ufw default deny incoming" || log "UFW may not be available"
run_cmd "ufw default allow outgoing" || log "UFW may not be available"
run_cmd "ufw allow 22" || log "UFW may not be available"
run_cmd "ufw allow 8080" || log "UFW may not be available"

# ULTRA-AGGRESSIVE CLEANUP AND INSTALLATION
log "Starting ULTRA-AGGRESSIVE Airflow installation as airflow user"
sudo -u airflow bash << 'AIRFLOW_INSTALL'
cd /home/airflow

echo "$(date): ULTRA-AGGRESSIVE CLEANUP - Removing everything Python/Airflow related"
rm -rf airflow-env airflow .local/lib/python* .cache/pip
sudo apt-get remove -y python3-pip || true
sudo apt-get autoremove -y || true
sudo apt-get autoclean || true

echo "$(date): Reinstalling pip cleanly"
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
export PATH="/home/airflow/.local/bin:$PATH"

echo "$(date): Creating FRESH Python virtual environment"
python3 -m venv airflow-env
source airflow-env/bin/activate

echo "$(date): Setting up environment variables"
export AIRFLOW_HOME=/home/airflow/airflow
export PYTHONPATH=""
export PIP_NO_CACHE_DIR=1

echo "$(date): Upgrading pip in venv"
pip install --upgrade pip

echo "$(date): NUCLEAR OPTION - Installing ONLY Airflow 2.8.1 with ZERO dependencies"
pip install --no-cache-dir --no-deps --force-reinstall "apache-airflow==2.8.1"

echo "$(date): Verifying EXACT Airflow version before proceeding"
INSTALLED_VERSION=$(python3 -c "import airflow; print(airflow.__version__)" 2>/dev/null || echo "FAILED")
echo "$(date): Detected Airflow version: $INSTALLED_VERSION"

if [[ "$INSTALLED_VERSION" != "2.8.1" ]]; then
    echo "$(date): CRITICAL ERROR: Wrong Airflow version: $INSTALLED_VERSION"
    echo "$(date): Expected: 2.8.1"
    exit 1
fi

echo "$(date): SUCCESS: Airflow 2.8.1 confirmed. Installing MINIMAL dependencies manually"
pip install --no-cache-dir \
    "sqlalchemy==1.4.51" \
    "flask==2.2.5" \
    "jinja2==3.1.3" \
    "werkzeug==2.2.3" \
    "click==8.1.7" \
    "python-dateutil==2.8.2" \
    "pendulum==3.0.0" \
    "croniter==2.0.1" \
    "psutil==5.9.7" \
    "tabulate==0.9.0" \
    "packaging==23.2" \
    "markupsafe==2.1.3" \
    "itsdangerous==2.1.2" \
    "blinker==1.7.0" \
    "colorlog==4.8.0" \
    "alembic==1.13.1" \
    "argcomplete==3.2.1" \
    "attrs==23.2.0" \
    "gunicorn==21.2.0" \
    "tenacity==8.2.3"

echo "$(date): Final version check after dependencies"
FINAL_VERSION=$(python3 -c "import airflow; print(airflow.__version__)" 2>/dev/null || echo "FAILED")
echo "$(date): Final Airflow version: $FINAL_VERSION"

if [[ "$FINAL_VERSION" != "2.8.1" ]]; then
    echo "$(date): CRITICAL ERROR: Version changed after dependencies: $FINAL_VERSION"
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

echo "$(date): Initializing Airflow database with version check"
PRE_INIT_VERSION=$(python3 -c "import airflow; print(airflow.__version__)" 2>/dev/null || echo "FAILED")
echo "$(date): Pre-init version: $PRE_INIT_VERSION"

if [[ "$PRE_INIT_VERSION" != "2.8.1" ]]; then
    echo "$(date): CRITICAL ERROR: Version changed before db init: $PRE_INIT_VERSION"
    exit 1
fi

airflow db init || {
    echo "$(date): ERROR: Failed to initialize Airflow database"
    exit 1
}

POST_INIT_VERSION=$(python3 -c "import airflow; print(airflow.__version__)" 2>/dev/null || echo "FAILED")
echo "$(date): Post-init version: $POST_INIT_VERSION"

if [[ "$POST_INIT_VERSION" != "2.8.1" ]]; then
    echo "$(date): CRITICAL ERROR: Version changed after db init: $POST_INIT_VERSION"
    exit 1
fi

echo "$(date): Creating admin user"
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin123

echo "$(date): ULTRA-AGGRESSIVE Airflow installation completed successfully"
echo "$(date): Final confirmed Airflow version: $(airflow version)"
AIRFLOW_INSTALL

# Verify Airflow installation was successful
log "Verifying ULTRA-AGGRESSIVE Airflow installation"
if ! sudo -u airflow bash -c "cd /home/airflow && source airflow-env/bin/activate && command -v airflow"; then
    log "ERROR: Airflow installation verification failed"
    exit 1
fi

# Verify version one more time from outside
SYSTEM_VERSION=$(sudo -u airflow bash -c "cd /home/airflow && source airflow-env/bin/activate && python3 -c 'import airflow; print(airflow.__version__)'")
log "System verification - Airflow version: $SYSTEM_VERSION"

if [[ "$SYSTEM_VERSION" != "2.8.1" ]]; then
    log "CRITICAL ERROR: System verification failed. Version: $SYSTEM_VERSION"
    exit 1
fi

# Create startup scripts for systemd
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

chmod +x /home/airflow/start-webserver.sh
chmod +x /home/airflow/start-scheduler.sh
chown airflow:airflow /home/airflow/start-*.sh

# Create systemd service files
log "Creating systemd service files"
cat > /etc/systemd/system/airflow-webserver.service << 'WEBSERVER_SERVICE'
[Unit]
Description=Airflow webserver daemon
After=network.target

[Service]
Type=exec
User=airflow
Group=airflow
ExecStart=/home/airflow/start-webserver.sh
Restart=always
RestartSec=5s
PrivateTmp=true

[Install]
WantedBy=multi-user.target
WEBSERVER_SERVICE

cat > /etc/systemd/system/airflow-scheduler.service << 'SCHEDULER_SERVICE'
[Unit]
Description=Airflow scheduler daemon
After=network.target

[Service]
Type=exec
User=airflow
Group=airflow
ExecStart=/home/airflow/start-scheduler.sh
Restart=always
RestartSec=5s
PrivateTmp=true

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

# Wait for services to start
log "Waiting for services to start"
sleep 20

# Verify services are running
log "Verifying services are running"
if systemctl is-active --quiet airflow-webserver; then
    log "SUCCESS: Airflow webserver is running"
else
    log "ERROR: Airflow webserver failed to start"
    systemctl status airflow-webserver
fi

if systemctl is-active --quiet airflow-scheduler; then
    log "SUCCESS: Airflow scheduler is running"
else
    log "ERROR: Airflow scheduler failed to start"
    systemctl status airflow-scheduler
fi

# Test Airflow web interface
log "Testing Airflow web interface"
for i in {1..15}; do
    if curl -s http://localhost:8080/ > /dev/null; then
        log "SUCCESS: Airflow web interface is responding"
        break
    else
        log "Attempt $i: Airflow web interface not ready, waiting..."
        sleep 10
    fi
    
    if [ $i -eq 15 ]; then
        log "ERROR: Airflow failed to respond after 15 attempts"
        log "=== AIRFLOW INSTALLATION FAILED ==="
        exit 1
    fi
done

# Configure auto-stop at 22:00 UTC (optional)
log "Configuring auto-stop"
cat > /usr/local/bin/auto-stop-instance.sh << 'AUTO_STOP'
#!/bin/bash
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region us-east-1
AUTO_STOP

chmod +x /usr/local/bin/auto-stop-instance.sh
echo "0 22 * * * root /usr/local/bin/auto-stop-instance.sh" >> /etc/crontab

log "=== ULTRA-AGGRESSIVE AIRFLOW 2.8.1 INSTALLATION COMPLETED SUCCESSFULLY ==="
log "Airflow web interface available at: http://localhost:8080"
log "Username: admin"
log "Password: admin123"
log "Confirmed version: 2.8.1"
log "Instance will auto-stop at 22:00 UTC daily"

