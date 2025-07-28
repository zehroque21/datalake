# Data Lake Local Development Environment

Complete local development environment for the Data Lake project with modern data stack:

## 🛠️ Technology Stack

- **🌊 Orchestration:** Prefect 2.14.21
- **📊 Visualization:** Apache Superset
- **📚 Data Catalog:** OpenMetadata
- **⚡ Processing:** Apache Spark with Delta Lake
- **🗂️ Storage:** Delta Lake format (ACID transactions)
- **🐳 Infrastructure:** Docker Compose

## 🚀 Quick Start

```bash
# Start the complete Data Lake environment
./start-datalake.sh

# Access the tools
open http://localhost:4200  # Prefect UI
open http://localhost:8088  # Superset (admin/admin123)
open http://localhost:8585  # OpenMetadata
open http://localhost:8080  # Spark UI
```

## 🌐 Access Points

| Tool | URL | Credentials | Purpose |
|------|-----|-------------|---------|
| **Prefect** | http://localhost:4200 | - | Workflow orchestration |
| **Superset** | http://localhost:8088 | admin/admin123 | Data visualization & dashboards |
| **OpenMetadata** | http://localhost:8585 | - | Data catalog & governance |
| **Spark UI** | http://localhost:8080 | - | Spark job monitoring |

## 📁 Data Lake Architecture

```
/app/s3/
├── staging/     # 📥 Raw data as received (JSON/CSV)
├── raw/         # 🗂️ Delta Lake tables (validated data)
├── trusted/     # ✅ Processed and enriched data
└── refined/     # 📊 Analytics-ready aggregations
```

## 🌡️ Temperature Pipeline

Automated pipeline that:
- Collects real-time temperature data for Campinas, SP
- Validates data quality
- Stores in staging (JSON) and raw (Delta Lake)
- Runs every 30 minutes automatically
- Provides metadata and lineage tracking

## 🔍 Useful Commands

```bash
# View pipeline logs
docker compose logs -f prefect-server

# Check latest temperature data
docker compose exec prefect-server cat /app/s3/staging/weather/campinas_temperature_latest.json

# View Delta table metadata
docker compose exec prefect-server cat /app/s3/raw/weather/campinas_temperature_metadata.json

# Explore S3 structure
docker compose exec prefect-server find /app/s3 -type f

# Stop environment
docker compose down
```

## 🗂️ Delta Lake Benefits

- **ACID Transactions:** Reliable data operations
- **Time Travel:** Query historical versions
- **Schema Evolution:** Automatic schema updates
- **Unified Batch/Stream:** Single format for all data
- **Metadata:** Rich table statistics and lineage

## 📊 Data Visualization

### Superset Setup
1. Access http://localhost:8088
2. Login with admin/admin123
3. Connect to Delta tables via Spark SQL
4. Create dashboards for temperature monitoring

### OpenMetadata Setup
1. Access http://localhost:8585
2. Discover datasets automatically
3. View data lineage and quality metrics
4. Manage data governance policies

## 🔄 Development Workflow

1. **Develop:** Edit flows in `/flows/` directory
2. **Test:** Run `./start-datalake.sh` to test locally
3. **Monitor:** Use Prefect UI to track pipeline execution
4. **Visualize:** Create dashboards in Superset
5. **Govern:** Manage metadata in OpenMetadata

## 🐳 Docker Services

- **prefect-server:** Main orchestration engine
- **superset:** Data visualization platform
- **superset-db:** PostgreSQL for Superset
- **openmetadata:** Data catalog service
- **openmetadata-db:** PostgreSQL for OpenMetadata
- **elasticsearch:** Search engine for metadata
- **spark:** Processing engine for Delta Lake

## 📈 Monitoring

- **Pipeline Health:** Prefect UI dashboard
- **Data Quality:** OpenMetadata quality metrics
- **Performance:** Spark UI for job monitoring
- **Visualization:** Superset dashboards

## 🔧 Troubleshooting

```bash
# Restart specific service
docker compose restart prefect-server

# View service logs
docker compose logs superset

# Clean restart
docker compose down -v && ./start-datalake.sh

# Check service health
docker compose ps
```

## 🎯 Next Steps

1. Add more data sources to the pipeline
2. Create trusted layer transformations
3. Build refined layer aggregations
4. Develop business intelligence dashboards
5. Implement data quality monitoring

