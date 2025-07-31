# 🌊 DataLake Native

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

A lightweight, file-based data lake solution with modern web dashboard for real-time monitoring and job orchestration.

## 🚀 Overview

DataLake Native is a simplified, production-ready data lake implementation that focuses on:

- **File-based storage** - No database dependencies, S3-compatible
- **Real-time monitoring** - Modern web dashboard with live metrics
- **Job orchestration** - Built-in scheduler with execution tracking
- **Weather data collection** - Example pipeline for meteorological data
- **Containerized deployment** - Docker-ready for any environment

## 🏗️ Architecture

```
DataLake Native
├── 📊 Web Dashboard (Flask + Alpine.js)
├── 🔄 Job Scheduler (APScheduler)
├── 📁 File Storage (JSON-based)
├── 🌡️ Weather Collection Pipeline
└── 📈 Real-time Metrics & Monitoring
```

### Storage Structure
```
data/
├── raw/weather/          # Raw weather data (JSON)
├── processed/            # Processed datasets
├── logs/                 # Job execution logs
└── metrics/              # Calculated metrics
```

## ✨ Features

### 🎯 Core Features
- **Zero-dependency storage** - Pure file-based approach
- **Real-time dashboard** - Live metrics and data visualization
- **Job scheduling** - Automated data collection every 30 minutes
- **Manual triggers** - On-demand job execution
- **Error handling** - Comprehensive logging and error tracking
- **Responsive design** - Works on desktop and mobile

### 📊 Dashboard Features
- **Analytics Tab** - Metrics cards, temperature trends, recent executions
- **Jobs Tab** - Pipeline visualization, execution history, manual triggers
- **Modern UI** - Glassmorphism design with fintech-inspired aesthetics
- **Auto-refresh** - Real-time data updates every 30 seconds

### 🔄 Data Pipeline
- **Weather Collection** - Fetches data from OpenWeatherMap API
- **Data Validation** - Ensures data quality and consistency
- **JSON Storage** - Structured file-based persistence
- **Execution Tracking** - Detailed logs with performance metrics

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Docker (optional)
- OpenWeatherMap API key

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/zehroque21/datalake.git
   cd datalake
   ```

2. **Navigate to native solution**
   ```bash
   cd docker/native
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export OPENWEATHER_API_KEY="your_api_key_here"
   export DATA_DIR="./data"
   ```

5. **Run the application**
   ```bash
   ./start-native.sh
   ```

6. **Access the dashboard**
   ```
   http://localhost:5420
   ```

### Docker Deployment

1. **Build and run with Docker**
   ```bash
   cd docker/native
   docker-compose -f docker-compose-native.yml up -d
   ```

2. **Access the dashboard**
   ```
   http://localhost:5420
   ```

## 📖 Usage

### Dashboard Navigation

#### Analytics Tab
- **Metrics Overview** - Jobs today, success rate, total jobs, current temperature
- **Temperature Chart** - 24-hour temperature trend visualization
- **Recent Executions** - Last 10 job executions with status and timing

#### Jobs Tab
- **Pipeline DAG** - Visual representation of the data collection workflow
- **Pipeline Status** - Next run time, frequency, last execution status
- **Execution History** - Detailed job execution logs with error handling

### API Endpoints

- `GET /api/metrics` - System metrics and statistics
- `GET /api/weather` - Weather data from last 24 hours
- `GET /api/jobs` - Job execution history
- `POST /api/jobs/trigger/{job_name}` - Manual job execution

### Manual Job Execution

```bash
# Trigger weather collection job
curl -X POST http://localhost:5420/api/jobs/trigger/weather_collection
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | Required |
| `DATA_DIR` | Data storage directory | `./data` |
| `STORAGE_TYPE` | Storage backend type | `local` |
| `FLASK_ENV` | Flask environment | `production` |
| `PORT` | Application port | `5420` |

### Storage Configuration

The application supports different storage backends:

- **Local Files** - JSON files in local filesystem
- **S3 Compatible** - Ready for AWS S3, MinIO, etc.

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   export FLASK_ENV=production
   export OPENWEATHER_API_KEY="your_production_key"
   export DATA_DIR="/app/data"
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5420 app:app
   ```

### Cloud Deployment

The application is designed to be cloud-native and can be deployed on:

- **AWS** - EC2, ECS, Lambda
- **Google Cloud** - Compute Engine, Cloud Run
- **Azure** - Container Instances, App Service
- **Heroku** - Direct deployment support

### S3 Integration

To use S3 storage, update the configuration:

```python
STORAGE_TYPE = 's3'
S3_BUCKET = 'your-datalake-bucket'
AWS_REGION = 'us-east-1'
```

## 📊 Monitoring

### Health Checks

- `GET /health` - Application health status
- `GET /api/metrics` - System metrics

### Logging

Logs are structured and include:
- Job execution details
- Performance metrics
- Error tracking
- API request logs

### Metrics

The dashboard provides real-time metrics:
- Jobs executed today
- Success rate percentage
- Total job count
- Current temperature
- Execution duration trends

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenWeatherMap** - Weather data API
- **Flask** - Web framework
- **Alpine.js** - Reactive frontend framework
- **Chart.js** - Data visualization
- **Tailwind CSS** - Utility-first CSS framework

## 📞 Support

For support and questions:

- 📧 Email: muja.dr21@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/zehroque21/datalake/issues)
- 📖 Documentation: [GitHub Pages](https://zehroque21.github.io/datalake/)

---

**Built with ❤️ by Amado Roque**

