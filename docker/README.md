# Prefect Local Development Environment

This Docker environment provides a complete Prefect setup for local development with automatic pipeline execution.

## 🚀 Quick Start

```bash
# Start Prefect with automatic temperature monitoring
./test-prefect.sh

# Access Prefect UI
open http://localhost:4200
```

## 🌡️ Automatic Temperature Pipeline

When you start the Docker environment, it automatically:

1. **Starts Prefect server** on port 4200
2. **Runs temperature pipeline** immediately 
3. **Schedules recurring runs** every 30 minutes
4. **Stores data** in persistent volumes

### Pipeline Features

- **Real weather data** from Campinas, SP, Brazil
- **Data validation** and quality scoring
- **Persistent storage** in CSV and JSON formats
- **Summary statistics** and monitoring
- **Error handling** with fallback mock data

## 📊 Data Access

```bash
# View latest temperature reading
docker compose exec prefect-server cat /app/data/campinas_temperature_latest.json

# View temperature history
docker compose exec prefect-server head /app/data/campinas_temperature_history.csv

# View container logs
docker compose logs -f
```

## 🔧 Development Workflow

### Single Flows Directory

- **No more confusion**: Only one `flows/` directory in the root
- **Shared between local and cloud**: Same flows run everywhere
- **Organized structure**: Flows categorized by purpose

```
flows/
├── weather/                    # Weather-related pipelines
│   ├── campinas_temperature.py # Main temperature pipeline
│   └── deploy_temperature_flow.py # Auto-deployment script
├── examples/                   # Tutorial flows
├── etl/                       # Production ETL pipelines
├── ml/                        # Machine Learning workflows
└── monitoring/                # Data quality monitoring
```

### Making Changes

1. **Edit flows** directly in `flows/` directory
2. **Test locally** with Docker
3. **Commit changes** - same flows deploy to cloud
4. **No sync needed** - single source of truth

## 🐳 Docker Commands

```bash
# Start environment
./test-prefect.sh

# Stop environment  
docker compose down

# Rebuild after changes
docker compose down -v
docker compose build --no-cache
docker compose up -d

# View logs
docker compose logs -f prefect-server

# Access container shell
docker compose exec prefect-server bash
```

## 🌐 Prefect UI Features

Access http://localhost:4200 to see:

- **Flow runs** in real-time
- **Temperature data** visualization  
- **Pipeline logs** and debugging
- **Scheduling** management
- **Data quality** monitoring

## 📈 Pipeline Monitoring

The temperature pipeline provides:

- **Current conditions** for Campinas
- **Historical trends** and statistics
- **Data quality scores** and validation
- **Automatic error recovery** with mock data
- **Summary reports** with key metrics

## 🔄 Automatic Features

When Docker starts:

1. ✅ **Prefect server** starts automatically
2. ✅ **Worker pool** created and started  
3. ✅ **Temperature pipeline** runs immediately
4. ✅ **Scheduled execution** every 30 minutes
5. ✅ **Data persistence** across container restarts
6. ✅ **Health checks** and monitoring

## 🎯 Next Steps

1. **View the UI** at http://localhost:4200
2. **Check temperature data** in `/app/data/`
3. **Create new flows** in `flows/` directory
4. **Deploy to cloud** via GitHub Actions

The environment is designed to be **zero-configuration** - just run `./test-prefect.sh` and start building!

