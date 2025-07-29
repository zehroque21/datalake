#!/bin/bash
set -e

echo "🌊 Starting Data Lake environment with Prefect orchestration..."

# Set Prefect configuration
export PREFECT_API_URL="http://localhost:4200/api"
export PREFECT_SERVER_API_HOST="0.0.0.0"
export PREFECT_SERVER_API_PORT="4200"

# Start Prefect server in background
echo "🚀 Starting Prefect server..."
prefect server start --host 0.0.0.0 --port 4200 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for Prefect server to be ready..."
sleep 15

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

# Run the Delta temperature pipeline immediately on startup
echo "🌡️ Running initial Campinas Temperature Delta Pipeline..."
cd /app/flows
python -c "
import sys
sys.path.append('/app/flows')
from weather.campinas_temperature_delta import campinas_temperature_delta_pipeline
try:
    result = campinas_temperature_delta_pipeline()
    print(f'🎉 Initial Delta pipeline completed: {result[\"status\"]}')
    print(f'🗂️ Delta path: {result[\"delta_path\"]}')
    print(f'📋 Records: {result[\"metadata\"].get(\"record_count\", \"unknown\")}')
except Exception as e:
    print(f'❌ Pipeline error: {e}')
"

# Deploy the temperature pipeline with scheduling
echo "📅 Deploying scheduled temperature monitoring..."
cd /app/flows
python -c "
import sys
sys.path.append('/app/flows')
from weather.campinas_temperature import campinas_temperature_pipeline
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import IntervalSchedule
from datetime import timedelta

try:
    deployment = Deployment.build_from_flow(
        flow=campinas_temperature_pipeline,
        name='campinas-temperature-monitor',
        schedule=IntervalSchedule(interval=timedelta(minutes=30)),
        work_pool_name='default-agent-pool'
    )
    deployment.apply()
    print('✅ Temperature monitoring deployment created successfully!')
except Exception as e:
    print(f'❌ Deployment error: {e}')"" &
DEPLOY_PID=$!

echo "🎉 Data Lake environment fully initialized!"
echo "🌐 Prefect UI available at: http://localhost:4200"
echo "📊 Apache Superset available at: http://localhost:8088 (admin/admin123)"
echo "📚 OpenMetadata available at: http://localhost:8585"
echo "⚡ Spark UI available at: http://localhost:8080"
echo ""
echo "🌡️ Temperature pipeline is running automatically every 30 minutes"
echo "🗂️ Data is being stored in JSON/CSV format in /app/s3/"
echo ""
echo "🔍 To view the data:"
echo "   Staging: docker compose exec prefect-server cat /app/s3/staging/weather/campinas_temperature_latest.json"
echo "   Delta:   docker compose exec prefect-server ls -la /app/s3/raw/weather/"
echo "   Metadata: docker compose exec prefect-server cat /app/s3/raw/weather/campinas_temperature_metadata.json"

# Keep the container running
wait $SERVER_PID $WORKER_PID $DEPLOY_PID

