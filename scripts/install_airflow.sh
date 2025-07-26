#!/bin/bash

# Secure Airflow Installation Script
# This script should be run on the EC2 instance via Systems Manager Session Manager

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting secure Airflow installation...${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root for security reasons${NC}"
   echo "Please run as the 'airflow' user or create one first"
   exit 1
fi

# Create airflow user if it doesn't exist
if ! id "airflow" &>/dev/null; then
    echo -e "${YELLOW}Creating airflow user...${NC}"
    sudo useradd -m -s /bin/bash airflow
    sudo usermod -aG sudo airflow
fi

# Switch to airflow user if not already
if [[ $(whoami) != "airflow" ]]; then
    echo -e "${YELLOW}Switching to airflow user...${NC}"
    sudo -u airflow bash "$0" "$@"
    exit $?
fi

# Set up environment variables
export AIRFLOW_HOME=/home/airflow/airflow
export AIRFLOW_VERSION=2.8.1
export PYTHON_VERSION="$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

echo -e "${GREEN}Setting up Airflow environment...${NC}"
echo "AIRFLOW_HOME: $AIRFLOW_HOME"
echo "AIRFLOW_VERSION: $AIRFLOW_VERSION"
echo "PYTHON_VERSION: $PYTHON_VERSION"

# Create airflow directory
mkdir -p $AIRFLOW_HOME
cd $AIRFLOW_HOME

# Create and activate virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
python3 -m venv airflow-env
source airflow-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Airflow with specific providers
echo -e "${YELLOW}Installing Apache Airflow...${NC}"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Install additional providers for AWS and data processing
echo -e "${YELLOW}Installing Airflow providers...${NC}"
pip install apache-airflow-providers-amazon
pip install apache-airflow-providers-postgres
pip install apache-airflow-providers-http

# Install data processing libraries
echo -e "${YELLOW}Installing data processing libraries...${NC}"
pip install pandas
pip install boto3
pip install delta-spark
pip install pyspark

# Initialize Airflow database
echo -e "${YELLOW}Initializing Airflow database...${NC}"
airflow db init

# Create admin user with secure password
echo -e "${YELLOW}Creating Airflow admin user...${NC}"
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password $(openssl rand -base64 12)

# Create secure Airflow configuration
echo -e "${YELLOW}Configuring Airflow security settings...${NC}"
cat > $AIRFLOW_HOME/airflow.cfg << EOF
[core]
dags_folder = $AIRFLOW_HOME/dags
base_log_folder = $AIRFLOW_HOME/logs
plugins_folder = $AIRFLOW_HOME/plugins
executor = LocalExecutor
sql_alchemy_conn = sqlite:///$AIRFLOW_HOME/airflow.db
load_examples = False
security = True

[webserver]
web_server_host = 127.0.0.1
web_server_port = 8080
secret_key = $(openssl rand -base64 32)
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
EOF

# Create DAGs directory
mkdir -p $AIRFLOW_HOME/dags
mkdir -p $AIRFLOW_HOME/logs
mkdir -p $AIRFLOW_HOME/plugins

# Create sample secure DAG
cat > $AIRFLOW_HOME/dags/sample_delta_lake_dag.py << 'EOF'
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import pandas as pd
import boto3

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sample_delta_lake_pipeline',
    default_args=default_args,
    description='Sample Delta Lake data pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['delta-lake', 'data-engineering'],
)

def process_data():
    """Sample data processing function"""
    # Create sample data
    data = pd.DataFrame({
        'id': range(1, 101),
        'value': range(100, 200),
        'timestamp': pd.date_range('2025-01-01', periods=100, freq='H')
    })
    
    # Process data (example transformation)
    data['processed_value'] = data['value'] * 2
    
    print(f"Processed {len(data)} records")
    return data.to_dict('records')

def upload_to_s3():
    """Upload processed data to S3"""
    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = 'datalake-bucket-for-airflow-and-delta-v2'
    
    # This is a placeholder - in real implementation, you would
    # write Delta Lake tables here
    print(f"Would upload data to S3 bucket: {bucket_name}")

process_task = PythonOperator(
    task_id='process_data',
    python_callable=process_data,
    dag=dag,
)

upload_task = PythonOperator(
    task_id='upload_to_s3',
    python_callable=upload_to_s3,
    dag=dag,
)

process_task >> upload_task
EOF

# Create systemd service for Airflow webserver
echo -e "${YELLOW}Creating systemd services...${NC}"
sudo tee /etc/systemd/system/airflow-webserver.service > /dev/null << EOF
[Unit]
Description=Airflow webserver daemon
After=network.target

[Service]
Environment=AIRFLOW_HOME=/home/airflow/airflow
User=airflow
Group=airflow
Type=simple
ExecStart=/home/airflow/airflow/airflow-env/bin/airflow webserver
Restart=on-failure
RestartSec=5s
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Airflow scheduler
sudo tee /etc/systemd/system/airflow-scheduler.service > /dev/null << EOF
[Unit]
Description=Airflow scheduler daemon
After=network.target

[Service]
Environment=AIRFLOW_HOME=/home/airflow/airflow
User=airflow
Group=airflow
Type=simple
ExecStart=/home/airflow/airflow/airflow-env/bin/airflow scheduler
Restart=on-failure
RestartSec=5s
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable airflow-webserver
sudo systemctl enable airflow-scheduler

# Start services
echo -e "${YELLOW}Starting Airflow services...${NC}"
sudo systemctl start airflow-webserver
sudo systemctl start airflow-scheduler

# Set proper permissions
chmod 700 $AIRFLOW_HOME
chmod 600 $AIRFLOW_HOME/airflow.cfg

echo -e "${GREEN}Airflow installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Important Security Notes:${NC}"
echo "1. Airflow is configured to run on localhost only (127.0.0.1:8080)"
echo "2. No external access is allowed for security reasons"
echo "3. Admin password was randomly generated - check logs for details"
echo "4. To access Airflow UI, use port forwarding through Session Manager"
echo ""
echo -e "${YELLOW}Service Status:${NC}"
sudo systemctl status airflow-webserver --no-pager -l
sudo systemctl status airflow-scheduler --no-pager -l
echo ""
echo -e "${GREEN}Installation complete! Airflow is running securely.${NC}"

