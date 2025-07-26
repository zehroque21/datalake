# DataLake AWS - Data Engineering Platform

🌐 **[Visit the project page](https://zehroque21.github.io/datalake/)** for a complete overview of the solution.

---

This repository contains a complete datalake solution that combines data engineering best practices with infrastructure as code (IaC). The platform provides a robust environment for data processing and analysis at scale, using Apache Airflow for orchestration and Delta Lake for reliable storage.

## 🚀 Overview

The solution automatically provisions a modern datalake infrastructure on Amazon Web Services (AWS), integrating:

- **Apache Airflow** for data pipeline orchestration
- **Delta Lake** for transactional and versioned storage
- **AWS S3** for scalable and durable storage
- **EC2** optimized for data processing
- **CI/CD** integrated via GitHub Actions

## 🏗️ Provisioned Infrastructure

Terraform provisions the following resources on AWS:

### 1. EC2 Instance (`aws_instance.airflow_vm`)
- **Type:** `t3.micro` (optimized for data workloads)
- **AMI:** Ubuntu Server 22.04 LTS (dynamically selected)
- **Purpose:** Host for Apache Airflow, Python scripts, Spark, and other processing tools

### 2. S3 Bucket (`data.aws_s3_bucket.datalake`)
- **Name:** `datalake-bucket-for-airflow-and-delta-v2`
- **Purpose:** Primary datalake storage for raw data, processed data, and Delta Lake tables

## ⚙️ Automation and Deployment

### GitHub Actions Workflow

The automated pipeline (`/.github/workflows/terraform.yaml`) executes:

1. **Resource Cleanup:** Removes old instances to optimize costs
2. **Validation:** Formats, validates, and plans Terraform changes
3. **Provisioning:** Applies infrastructure on AWS
4. **Outputs:** Displays information about created resources

**Triggers:**
- Push to `main` branch (only files in `/terraform/`)
- Pull Requests to `main`

### Credentials Configuration

Configure the following GitHub Secrets:
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## 📁 Project Structure

```
├── terraform/                 # Infrastructure as code
│   ├── main.tf               # Main resources (EC2, S3)
│   ├── variables.tf          # Terraform variables
│   └── outputs.tf            # Resource outputs
├── scripts/                  # Configuration scripts and examples
│   ├── install_airflow.sh    # Apache Airflow installation
│   └── delta_lake_examples/  # Delta Lake usage examples
│       ├── write_delta_table.py
│       └── read_delta_table.py
├── .github/workflows/        # CI/CD pipelines
│   └── terraform.yaml        # Main workflow
└── index.html               # Project page (GitHub Pages)
```

## 🛠️ Setup and Usage

### 1. Infrastructure Deployment
```bash
# Deployment is automatic via GitHub Actions
# Push changes to /terraform/ to trigger
git add terraform/
git commit -m "Update infrastructure"
git push origin main
```

### 2. EC2 Instance Access
```bash
# Connect via SSH (configure your SSH key on AWS)
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 3. Airflow Installation
```bash
# On the EC2 instance, run:
cd /path/to/repository
bash scripts/install_airflow.sh
```

### 4. Delta Lake Usage
```python
# Write example
python scripts/delta_lake_examples/write_delta_table.py

# Read example
python scripts/delta_lake_examples/read_delta_table.py
```

## 🔧 Technologies Used

- **Infrastructure:** Terraform, AWS (EC2, S3, IAM)
- **Orchestration:** Apache Airflow
- **Storage:** Delta Lake, AWS S3
- **Processing:** Python, Apache Spark
- **CI/CD:** GitHub Actions
- **Monitoring:** Airflow Web UI

## 📊 Solution Architecture

```
GitHub Actions → Terraform → AWS EC2 (Airflow) → AWS S3 (Delta Lake)
```

1. **Ingestion:** Data collection via Airflow pipelines
2. **Processing:** Transformations with Python/Spark
3. **Storage:** Data saved in Delta Lake format
4. **Analysis:** Queries and analytics on processed data

## 🎯 Use Cases

- **ETL/ELT Pipelines:** Automated data processing
- **Data Warehousing:** Structured storage for analytics
- **Real-time Analytics:** Stream data processing
- **Machine Learning:** Data preparation for ML models
- **Business Intelligence:** Dashboards and reports

## 👨‍💻 About the Creator

**Amado Roque** - Data Engineer specialized in big data and analytics solutions.

- 🔗 [LinkedIn](https://www.linkedin.com/in/amado-roque/)
- 🐙 [GitHub](https://github.com/zehroque21)

---

## 📄 License

This project is under the MIT license. See the [LICENSE](LICENSE) file for more details.

## 🤝 Contributions

Contributions are welcome! Feel free to open issues and pull requests.

---

**[🌐 Visit the project page](https://zehroque21.github.io/datalake/)** for more information and visual documentation.

