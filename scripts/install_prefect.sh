#!/bin/bash

# Prefect Installation Script for EC2
# Based on working Docker implementation

set -e

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a /var/log/prefect-install.log
}

log "🌊 Starting Prefect installation on EC2..."

# Update system
log "📦 Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install essential packages
log "🔧 Installing essential packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    htop \
    ufw \
    unzip

# Create prefect user
log "👤 Creating prefect user..."
useradd -m -s /bin/bash prefect

# Create prefect environment
log "🐍 Creating Python virtual environment..."
sudo -u prefect bash -c "
cd /home/prefect
python3 -m venv prefect-env
source prefect-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Prefect and dependencies
log '📦 Installing Prefect 2.14.21...'
pip install --no-cache-dir \
    prefect==2.14.21 \
    pandas==2.1.4 \
    boto3==1.34.0 \
    requests==2.31.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9

# Fix griffe version conflict (critical fix from Docker testing)
log '🔧 Fixing griffe version conflict...'
pip install --no-cache-dir griffe==0.38.1

# Verify installation
log '✅ Verifying Prefect installation...'
python -c 'import prefect; print(\"Prefect version:\", prefect.__version__); from prefect import flow; print(\"Import successful!\")'
"

# Set up Prefect configuration
log "⚙️ Setting up Prefect configuration..."
sudo -u prefect bash -c "
cd /home/prefect
source prefect-env/bin/activate

# Set environment variables
export PREFECT_API_URL=http://0.0.0.0:4200/api
export PREFECT_SERVER_API_HOST=0.0.0.0
export PREFECT_SERVER_API_PORT=4200

# Create prefect config directory
mkdir -p /home/prefect/.prefect

# Initialize database (this will create the SQLite database)
log '🗄️ Initializing Prefect database...'
prefect server database reset -y
"

# Create example flows directory
log "📁 Creating flows directory..."
sudo -u prefect mkdir -p /home/prefect/flows

# Create example flow
log "📝 Creating example data pipeline flow..."
sudo -u prefect tee /home/prefect/flows/example_pipeline.py > /dev/null << 'EOF'
"""
Example Data Pipeline with Prefect for EC2
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from prefect import flow, task
import json


@task
def extract_sample_data():
    """Extract sample data from a public API"""
    print("🔍 Extracting sample data...")
    
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/posts")
        data = response.json()
        print(f"✅ Extracted {len(data)} records")
        return data
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return []


@task
def transform_data(raw_data):
    """Transform the raw data"""
    print("🔄 Transforming data...")
    
    if not raw_data:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_data)
    
    # Add transformations
    df['title_length'] = df['title'].str.len()
    df['body_length'] = df['body'].str.len()
    df['created_at'] = datetime.now()
    df['word_count'] = df['body'].str.split().str.len()
    
    # Filter and clean
    df_clean = df[df['title_length'] > 10].copy()
    
    print(f"✅ Transformed data: {len(df_clean)} records after cleaning")
    return df_clean


@task
def load_data(transformed_data):
    """Load data to local storage"""
    print("💾 Loading data...")
    
    if transformed_data.empty:
        print("⚠️ No data to load")
        return {"status": "no_data"}
    
    # Save to local files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON
    json_path = f"/home/prefect/data/processed_data_{timestamp}.json"
    transformed_data.to_json(json_path, orient='records', indent=2)
    
    print(f"✅ Data saved to: {json_path}")
    
    return {
        "status": "success",
        "file_path": json_path,
        "record_count": len(transformed_data)
    }


@flow(name="EC2 Data Pipeline", description="Example ETL pipeline for EC2")
def ec2_data_pipeline():
    """Main ETL flow for EC2"""
    print("🚀 Starting EC2 Data Pipeline...")
    
    # Extract
    raw_data = extract_sample_data()
    
    # Transform
    clean_data = transform_data(raw_data)
    
    # Load
    result = load_data(clean_data)
    
    print("🎉 Pipeline completed successfully!")
    return result


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running flow locally for testing...")
    result = ec2_data_pipeline()
    print(f"🎯 Final result: {result}")
EOF

# Create data directory
sudo -u prefect mkdir -p /home/prefect/data

# Create systemd service for Prefect server
log "🔧 Creating Prefect server systemd service..."
tee /etc/systemd/system/prefect-server.service > /dev/null << EOF
[Unit]
Description=Prefect Server
After=network.target

[Service]
Type=exec
User=prefect
Group=prefect
WorkingDirectory=/home/prefect
Environment=PATH=/home/prefect/prefect-env/bin
Environment=PREFECT_API_URL=http://0.0.0.0:4200/api
Environment=PREFECT_SERVER_API_HOST=0.0.0.0
Environment=PREFECT_SERVER_API_PORT=4200
ExecStart=/home/prefect/prefect-env/bin/prefect server start --host 0.0.0.0 --port 4200
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Prefect worker
log "🔧 Creating Prefect worker systemd service..."
tee /etc/systemd/system/prefect-worker.service > /dev/null << EOF
[Unit]
Description=Prefect Worker
After=network.target prefect-server.service
Requires=prefect-server.service

[Service]
Type=exec
User=prefect
Group=prefect
WorkingDirectory=/home/prefect
Environment=PATH=/home/prefect/prefect-env/bin
Environment=PREFECT_API_URL=http://localhost:4200/api
ExecStartPre=/bin/sleep 30
ExecStartPre=/home/prefect/prefect-env/bin/prefect work-pool create --type process default-pool
ExecStart=/home/prefect/prefect-env/bin/prefect worker start --pool default-pool
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
log "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 4200/tcp

# Enable and start services
log "🚀 Enabling and starting Prefect services..."
systemctl daemon-reload
systemctl enable prefect-server
systemctl enable prefect-worker
systemctl start prefect-server

# Wait for server to start
log "⏳ Waiting for Prefect server to start..."
sleep 30

# Start worker
systemctl start prefect-worker

# Verify services
log "✅ Verifying Prefect services..."
sleep 10

if systemctl is-active --quiet prefect-server; then
    log "✅ Prefect server is running"
else
    log "❌ Prefect server failed to start"
    systemctl status prefect-server --no-pager
fi

if systemctl is-active --quiet prefect-worker; then
    log "✅ Prefect worker is running"
else
    log "❌ Prefect worker failed to start"
    systemctl status prefect-worker --no-pager
fi

# Test API connectivity
log "🔍 Testing Prefect API connectivity..."
if curl -s http://localhost:4200/api/health > /dev/null; then
    log "✅ Prefect API is responding"
else
    log "❌ Prefect API is not responding"
fi

# Auto-stop instance after 2 hours (optional)
log "⏰ Setting up auto-stop after 2 hours..."
echo "sudo shutdown -h now" | at now + 2 hours 2>/dev/null || log "⚠️ Could not set auto-stop (at command not available)"

log "🎉 Prefect installation completed successfully!"
log ""
log "📋 Access Information:"
log "   🌐 Prefect UI: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):4200"
log "   📊 Dashboard: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):4200/dashboard"
log "   🔧 API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):4200/api"
log ""
log "🔧 Service Management:"
log "   sudo systemctl status prefect-server"
log "   sudo systemctl status prefect-worker"
log "   sudo journalctl -u prefect-server -f"
log "   sudo journalctl -u prefect-worker -f"
log ""
log "🧪 Test Flow:"
log "   sudo -u prefect bash -c 'cd /home/prefect && source prefect-env/bin/activate && python flows/example_pipeline.py'"
log ""
log "🎯 Next Steps:"
log "   1. Access the Prefect UI via port forwarding or public IP"
log "   2. Create and deploy your data pipelines"
log "   3. Monitor flow runs in the dashboard"
log ""

