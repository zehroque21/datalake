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

# Create flows directory and copy from repository
log "📁 Setting up flows directory..."
sudo -u prefect mkdir -p /home/prefect/flows
sudo -u prefect cp -r /home/ubuntu/datalake/flows/* /home/prefect/flows/ 2>/dev/null || log "⚠️ No flows directory found in repository"

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
log "🧪 Test Flows:"
log "   sudo -u prefect bash -c 'cd /home/prefect && source prefect-env/bin/activate && python flows/examples/basic_etl_pipeline.py'"
log "   sudo -u prefect bash -c 'cd /home/prefect && source prefect-env/bin/activate && python flows/etl/s3_data_pipeline.py'"
log "   sudo -u prefect bash -c 'cd /home/prefect && source prefect-env/bin/activate && python flows/monitoring/data_quality_monitor.py'"
log ""
log "🎯 Next Steps:"
log "   1. Access the Prefect UI via port forwarding or public IP"
log "   2. Create and deploy your data pipelines"
log "   3. Monitor flow runs in the dashboard"
log ""

