#!/bin/bash

echo "🚀 Starting Prefect local test environment..."

# Function to check if service is ready
check_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "🔄 Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Build and start services
echo "🏗️ Building Prefect containers..."
docker compose build

echo "🚀 Starting Prefect services..."
docker compose up -d

# Check if Prefect server is ready
if check_service "http://localhost:4200/api/health" "Prefect Server"; then
    echo ""
    echo "🎉 Prefect environment is ready!"
    echo ""
    echo "📋 Access Information:"
    echo "   🌐 Prefect UI: http://localhost:4200"
    echo "   📊 Dashboard: http://localhost:4200/dashboard"
    echo "   🔧 API: http://localhost:4200/api"
    echo ""
    echo "🧪 Test Commands:"
    echo "   # Deploy example flows"
    echo "   docker compose exec prefect-server python /app/flows/example_data_pipeline.py"
    echo ""
    echo "   # Run a flow"
    echo "   docker compose exec prefect-server prefect deployment run 'Data Lake ETL Pipeline/default'"
    echo ""
    echo "   # View logs"
    echo "   docker compose logs -f prefect-server"
    echo "   docker compose logs -f prefect-agent"
    echo ""
    echo "   # Stop environment"
    echo "   docker compose down"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Open http://localhost:4200 in your browser"
    echo "   2. Explore the Prefect UI"
    echo "   3. Run the example flows"
    echo "   4. Create your own data pipelines!"
    echo ""
else
    echo "❌ Failed to start Prefect environment"
    echo "📋 Debug commands:"
    echo "   docker compose logs prefect-server"
    echo "   docker compose logs prefect-agent"
    exit 1
fi

