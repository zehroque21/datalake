#!/bin/bash
set -e

echo "🌊 Starting Prefect environment..."

# Set Prefect configuration
export PREFECT_API_URL="http://localhost:4200/api"
export PREFECT_SERVER_API_HOST="0.0.0.0"
export PREFECT_SERVER_API_PORT="4200"

# Create data directory
mkdir -p /app/data

# Start Prefect server in background
echo "🚀 Starting Prefect server..."
prefect server start --host 0.0.0.0 --port 4200 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for Prefect server to be ready..."
sleep 10

# Check if server is responding
for i in {1..30}; do
    if curl -s http://localhost:4200/api/health > /dev/null; then
        echo "✅ Prefect server is ready!"
        break
    fi
    echo "⏳ Waiting for server... ($i/30)"
    sleep 2
done

# Create default work pool
echo "🏊 Creating default work pool..."
prefect work-pool create default-agent-pool --type process || echo "Work pool already exists"

# Start Prefect worker in background
echo "👷 Starting Prefect worker..."
prefect worker start --pool default-agent-pool &
WORKER_PID=$!

# Wait a bit for worker to start
sleep 5

# Run the temperature pipeline immediately on startup (using staging version)
echo "🌡️ Running initial Campinas Temperature Pipeline (Local Staging)..."
cd /app/flows
python -c "
import sys
sys.path.append('/app/flows')
from weather.campinas_temperature_staging import campinas_temperature_staging_pipeline
try:
    result = campinas_temperature_staging_pipeline()
    print(f'🎉 Initial pipeline completed: {result[\"pipeline_status\"]}')
    print(f'🌡️ Temperature: {result[\"temperature_celsius\"]}°C')
    print(f'🌤️ Weather: {result[\"weather_description\"]}')
    print(f'💾 Data saved to staging: {result[\"staging_info\"][\"staging_base\"]}')
except Exception as e:
    print(f'❌ Pipeline error: {e}')
"

# Deploy the temperature pipeline with scheduling
echo "📅 Deploying scheduled temperature monitoring..."
python weather/deploy_temperature_flow.py &
DEPLOY_PID=$!

echo "🎉 Prefect environment fully initialized!"
echo "🌐 Prefect UI available at: http://localhost:4200"
echo "🌡️ Temperature pipeline is running automatically every 30 minutes"
echo "📊 Data is being stored in /app/data/"
echo ""
echo "🔍 To view the data:"
echo "   docker compose exec prefect-server cat /app/data/campinas_temperature_latest.json"
echo "   docker compose exec prefect-server head /app/data/campinas_temperature_history.csv"

# Keep the container running
wait $SERVER_PID $WORKER_PID $DEPLOY_PID

