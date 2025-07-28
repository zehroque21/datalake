#!/bin/bash

echo "🚀 Starting Prefect environment..."

# Wait for server to be ready if this is an agent
if [ "$1" = "agent" ]; then
    echo "⏳ Waiting for Prefect server to be ready..."
    sleep 15
fi

# Set Prefect configuration
export PREFECT_API_URL=${PREFECT_API_URL:-"http://localhost:4200/api"}

echo "🔧 Prefect API URL: $PREFECT_API_URL"

# Execute the command passed to the container
exec "$@"

