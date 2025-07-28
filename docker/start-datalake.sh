#!/bin/bash

echo "🏗️ Starting Data Lake Environment with Prefect, Superset, and OpenMetadata..."

# Stop existing containers and clean up orphans
echo "🛑 Stopping existing containers..."
docker compose down --remove-orphans

# Build and start the complete Data Lake environment
echo "🔨 Building and starting Data Lake environment..."
docker compose up -d --build

# Wait for Prefect server to be ready
echo "⏳ Waiting for Prefect server to be ready..."
sleep 30

# Check if Prefect is responding
for i in {1..20}; do
    if curl -s http://localhost:4200/api/health > /dev/null 2>&1; then
        echo "✅ Prefect server is ready!"
        break
    fi
    echo "⏳ Waiting for Prefect server... ($i/20)"
    sleep 3
done

# Check if temperature data is being collected
echo "🌡️ Checking temperature data collection..."
sleep 10

if docker compose exec -T prefect-server test -f /app/s3/staging/weather/campinas_temperature_latest.json; then
    echo "✅ Temperature staging data found!"
else
    echo "⚠️ Temperature staging data not found yet (may take a few minutes)"
fi

if docker compose exec -T prefect-server test -d /app/s3/raw/weather/campinas_temperature_delta; then
    echo "✅ Delta table created successfully!"
else
    echo "⚠️ Delta table not created yet (may take a few minutes)"
fi

echo ""
echo "🎉 Data Lake environment is running!"
echo ""
echo "🌐 Access Points:"
echo "   📊 Prefect UI:      http://localhost:4200"
echo "   📈 Superset:        http://localhost:8088 (admin/admin123)"
echo "   📚 OpenMetadata:    http://localhost:8585"
echo "   ⚡ Spark UI:        http://localhost:8080"
echo ""
echo "🌡️ Temperature pipeline is collecting data automatically"
echo ""
echo "🔍 Useful commands:"
echo "   View logs:              docker compose logs -f"
echo "   View latest temp:       docker compose exec prefect-server cat /app/s3/staging/weather/campinas_temperature_latest.json"
echo "   View Delta metadata:    docker compose exec prefect-server cat /app/s3/raw/weather/campinas_temperature_metadata.json"
echo "   View S3 structure:      docker compose exec prefect-server find /app/s3 -type f"
echo "   Stop environment:       docker compose down"
echo ""
echo "📊 The temperature pipeline runs automatically every 30 minutes!"
echo "💾 Data follows S3 structure: staging → raw (Delta) → trusted → refined!"
echo "🗂️ Raw layer uses Delta Lake format for ACID transactions and time travel!"

