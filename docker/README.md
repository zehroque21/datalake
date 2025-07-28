# Prefect Local Development Environment

This Docker environment provides a complete Prefect setup for local development with automatic pipeline execution and **AWS S3 integration**.

## 🚀 Quick Start

```bash
# 1. Configure AWS credentials (optional, for S3 integration)
cp .env.example .env
# Edit .env with your AWS credentials

# 2. Start Prefect with automatic temperature monitoring
./test-prefect.sh

# 3. Access Prefect UI
open http://localhost:4200
```

## ☁️ AWS S3 Integration

The environment supports both **local storage** and **AWS S3** for data persistence:

### Local Storage (Default)
- Data stored in Docker volumes
- No AWS credentials required
- Perfect for development and testing

### S3 Storage (Optional)
- Data stored in AWS S3 bucket
- Requires AWS credentials in `.env` file
- Production-ready data lake storage

### Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your AWS credentials:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

## 🌡️ Temperature Pipelines

Two temperature monitoring pipelines are available:

### 1. Local Storage Pipeline
- **File:** `flows/weather/campinas_temperature.py`
- **Storage:** Local CSV and JSON files
- **Usage:** Default pipeline, runs automatically

### 2. S3 Storage Pipeline  
- **File:** `flows/weather/campinas_temperature_s3.py`
- **Storage:** AWS S3 bucket (multiple formats)
- **Usage:** Requires AWS credentials

### S3 Storage Structure

When using S3, data is organized as:

```
s3://your-bucket/
├── weather/campinas/
│   ├── latest/
│   │   └── temperature.json          # Latest reading
│   ├── hourly/
│   │   └── 2025/01/28/
│   │       └── temperature_14.json   # Hourly readings
│   └── daily/
│       └── 2025/01/28/
│           └── temperature_history.csv # Daily aggregation
```

## 📊 Data Access

### Local Data
```bash
# View latest temperature reading
docker compose exec prefect-server cat /app/data/campinas_temperature_latest.json

# View temperature history
docker compose exec prefect-server head /app/data/campinas_temperature_history.csv
```

### S3 Data
```bash
# Using AWS CLI (if configured)
aws s3 cp s3://your-bucket/weather/campinas/latest/temperature.json -

# Or check in AWS Console
# Navigate to your S3 bucket → weather/campinas/latest/
```

## 🔧 Development Workflow

### Single Flows Directory

- **No more confusion**: Only one `flows/` directory in the root
- **Shared between local and cloud**: Same flows run everywhere  
- **Organized structure**: Flows categorized by purpose

```
flows/
├── weather/                    # Weather-related pipelines
│   ├── campinas_temperature.py # Local storage pipeline
│   ├── campinas_temperature_s3.py # S3 storage pipeline
│   └── deploy_temperature_flow.py # Auto-deployment script
├── examples/                   # Tutorial flows
├── etl/                       # Production ETL pipelines
├── ml/                        # Machine Learning workflows
└── monitoring/                # Data quality monitoring
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
- **S3 integration** for production data lake

## 🔄 Automatic Features

When Docker starts:

1. ✅ **Prefect server** starts automatically
2. ✅ **Worker pool** created and started  
3. ✅ **Temperature pipeline** runs immediately
4. ✅ **Scheduled execution** every 30 minutes
5. ✅ **Data persistence** (local or S3)
6. ✅ **Health checks** and monitoring

## 🎯 Next Steps

1. **View the UI** at http://localhost:4200
2. **Check temperature data** locally or in S3
3. **Configure AWS** for S3 integration (optional)
4. **Create new flows** in `flows/` directory
5. **Deploy to cloud** when ready (currently disabled)

## 🚫 AWS Deployment Disabled

AWS deployment via GitHub Actions is **temporarily disabled** for local development focus. The infrastructure code remains available for future use.

To re-enable AWS deployment:
1. Uncomment the workflow in `.github/workflows/terraform.yaml`
2. Configure GitHub secrets for AWS credentials
3. Push changes to trigger deployment

The environment is designed to be **zero-configuration** for local development - just run `./test-prefect.sh` and start building!

