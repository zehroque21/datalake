# Prefect Local Development Environment

This Docker environment provides a complete Prefect setup for local development with automatic pipeline execution and **local staging area** that simulates production data lake structure.

## 🚀 Quick Start

```bash
# Start Prefect with automatic temperature monitoring
./test-prefect.sh

# Access Prefect UI
open http://localhost:4200
```

## 💾 Local Staging Area

The environment uses a **local staging area** that simulates a production data lake structure:

### Staging Structure
```
/app/data/staging/
├── weather/campinas/
│   ├── latest/
│   │   └── temperature.json          # Latest reading
│   ├── hourly/
│   │   └── 2025/01/28/
│   │       └── temperature_14.json   # Hourly readings
│   ├── daily/
│   │   └── 2025/01/28/
│   │       └── temperature_history.csv # Daily aggregation
│   ├── monthly/
│   │   └── 2025/01/
│   │       └── summary.json          # Monthly statistics
│   └── raw/
│       └── 20250128_143022.json      # Raw timestamped data
```

### Benefits of Staging Approach
- **S3-like structure** for production readiness
- **Multiple data formats** (JSON, CSV) for different use cases
- **Time-based partitioning** for efficient data organization
- **Local development** without cloud dependencies
- **Easy migration** to real S3 when ready

## 🌡️ Temperature Pipeline

The automatic temperature monitoring pipeline:

### Features
- **Real weather data** from Campinas, SP, Brazil
- **Data validation** and quality scoring
- **Multiple storage formats** (latest, hourly, daily, monthly, raw)
- **S3-like organization** for production readiness
- **Error handling** with fallback mock data
- **Summary statistics** and monitoring

### Pipeline Flow
1. **Fetch** current temperature from wttr.in API
2. **Validate** and clean the data
3. **Create** staging directory structure
4. **Store** in multiple formats and locations
5. **Generate** summary statistics

## 📊 Data Access

```bash
# View latest temperature reading
docker compose exec prefect-server cat /app/data/staging/weather/campinas/latest/temperature.json

# View daily temperature history
docker compose exec prefect-server head /app/data/staging/weather/campinas/daily/*/temperature_history.csv

# View staging structure
docker compose exec prefect-server find /app/data/staging -type f

# View monthly summary
docker compose exec prefect-server cat /app/data/staging/weather/campinas/monthly/*/summary.json

# View container logs
docker compose logs -f
```

## 🔧 Development Workflow

### Single Flows Directory

- **No confusion**: Only one `flows/` directory in the root
- **Shared structure**: Same flows can be deployed to cloud later
- **Organized by purpose**: Flows categorized logically

```
flows/
├── weather/                           # Weather-related pipelines
│   ├── campinas_temperature.py       # Simple local storage
│   ├── campinas_temperature_staging.py # S3-like staging structure
│   └── deploy_temperature_flow.py    # Auto-deployment script
├── examples/                          # Tutorial flows
├── etl/                              # Production ETL pipelines
├── ml/                               # Machine Learning workflows
└── monitoring/                       # Data quality monitoring
```

### Making Changes

1. **Edit flows** directly in `flows/` directory
2. **Test locally** with Docker
3. **Commit changes** - same flows can deploy to cloud later
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
- **Staging area** with production-like structure

## 🔄 Automatic Features

When Docker starts:

1. ✅ **Prefect server** starts automatically
2. ✅ **Worker pool** created and started  
3. ✅ **Temperature pipeline** runs immediately
4. ✅ **Scheduled execution** every 30 minutes
5. ✅ **Staging area** created with S3-like structure
6. ✅ **Data persistence** across container restarts
7. ✅ **Health checks** and monitoring

## 🎯 Next Steps

1. **View the UI** at http://localhost:4200
2. **Check temperature data** in staging area
3. **Explore staging structure** with find commands
4. **Create new flows** in `flows/` directory
5. **Deploy to cloud** when ready (currently disabled)

## 🚫 AWS Deployment Disabled

AWS deployment via GitHub Actions is **temporarily disabled** for local development focus. The infrastructure code remains available for future use.

To re-enable AWS deployment:
1. Uncomment the workflow in `.github/workflows/terraform.yaml`
2. Configure GitHub secrets for AWS credentials
3. Push changes to trigger deployment

## 💡 Production Migration

When ready for production, the staging structure makes it easy to:

1. **Replace local paths** with S3 URLs
2. **Add AWS credentials** and boto3 integration  
3. **Keep same directory structure** in S3
4. **Minimal code changes** required

The environment is designed to be **zero-configuration** for local development while maintaining **production readiness**!

