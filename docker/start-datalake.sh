#!/bin/bash

echo "🏗️ Starting Data Lake Environment with Prefect Orchestration..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down --remove-orphans

# Build and start
echo "🔨 Building and starting Data Lake environment..."
docker compose build
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for Prefect server to be ready..."
sleep 30

# Check if Prefect UI is accessible
echo "🌐 Testing Prefect UI accessibility..."
if curl -s http://localhost:4200/api/health > /dev/null; then
    echo "✅ Prefect UI is accessible at http://localhost:4200"
else
    echo "❌ Prefect UI is not accessible"
    echo "📋 Container logs:"
    docker compose logs prefect-server
    exit 1
fi

# Check if temperature data was collected
echo "🌡️ Checking temperature data collection..."
sleep 10

# Check if data files exist
if docker compose exec -T prefect-server test -f /app/data/campinas_temperature_latest.json; then
    echo "✅ Temperature data files created successfully!"
    echo "📊 Latest temperature data:"
    docker compose exec -T prefect-server cat /app/data/campinas_temperature_latest.json | head -10
    echo ""
    echo "📈 Data files:"
    docker compose exec -T prefect-server ls -la /app/data/
else
    echo "⚠️ Temperature data files not found yet (may still be processing)"
fi

# Show container status
echo "📋 Container status:"
docker compose ps

echo ""
echo "🎉 Data Lake environment is running!"
echo "🌐 Access Prefect UI at: http://localhost:4200"
echo "🌡️ Temperature pipeline is collecting data automatically"
echo ""
echo "🔍 Useful commands:"
echo "   View logs:              docker compose logs -f"
echo "   View latest temp:       docker compose exec prefect-server cat /app/data/campinas_temperature_latest.json"
echo "   View history:           docker compose exec prefect-server head /app/data/campinas_temperature_history.csv"
echo "   View all data files:    docker compose exec prefect-server ls -la /app/data/"
echo "   Stop environment:       docker compose down"
echo ""
echo "📊 The temperature pipeline runs automatically every 30 minutes!"
echo "💾 Data is stored in simple JSON and CSV files!"

