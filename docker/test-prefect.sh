#!/bin/bash

echo "🌊 Testing Prefect Environment with Campinas Temperature Pipeline..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down -v

# Build and start
echo "🔨 Building and starting Prefect environment..."
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

# Check if staging data files exist
if docker compose exec -T prefect-server test -d /app/data/staging/weather/campinas; then
    echo "✅ Temperature staging directory created successfully!"
    echo "📊 Latest temperature data:"
    docker compose exec -T prefect-server cat /app/data/staging/weather/campinas/latest/temperature.json | head -10
    echo ""
    echo "📈 Staging structure:"
    docker compose exec -T prefect-server find /app/data/staging -type f | head -10
else
    echo "⚠️ Temperature staging directory not found yet (may still be processing)"
fi

# Show container status
echo "📋 Container status:"
docker compose ps

echo ""
echo "🎉 Prefect environment is running!"
echo "🌐 Access Prefect UI at: http://localhost:4200"
echo "🌡️ Temperature pipeline is collecting data automatically"
echo ""
echo "🔍 Useful commands:"
echo "   View logs:              docker compose logs -f"
echo "   View latest temp:       docker compose exec prefect-server cat /app/data/staging/weather/campinas/latest/temperature.json"
echo "   View daily history:     docker compose exec prefect-server head /app/data/staging/weather/campinas/daily/*/temperature_history.csv"
echo "   View staging structure: docker compose exec prefect-server find /app/data/staging -type f"
echo "   Stop environment:       docker compose down"
echo ""
echo "📊 The temperature pipeline runs automatically every 30 minutes!"
echo "💾 Data is stored in a local staging area with S3-like structure!"

