# DataLake AWS - Modern Data Engineering Platform

🌐 **[Visit the project page](https://zehroque21.github.io/datalake/)** for a complete overview of the solution.

🔒 **[Security Policy](SECURITY.md)** - Read our comprehensive security guidelines.

---

This repository contains a **secure** and complete datalake solution that combines modern data engineering best practices with infrastructure as code (IaC). The platform provides a robust and hardened environment for data processing and analysis at scale, using **Prefect** for orchestration and Delta Lake for reliable storage.

## 🚀 Overview

The solution automatically provisions a modern, **security-hardened** datalake infrastructure on Amazon Web Services (AWS), integrating:

- **🌊 Prefect** for modern data pipeline orchestration
- **📊 Delta Lake** for transactional and versioned storage
- **☁️ AWS S3** for scalable and durable storage
- **🖥️ EC2** optimized and hardened for data processing
- **🔄 CI/CD** integrated via GitHub Actions
- **🔒 Security-first** approach with no SSH access

## 🌊 Why Prefect?

We chose **Prefect** over traditional orchestrators for its modern approach:

- ✅ **Python-first** - Native Python workflows, no complex DAG syntax
- ✅ **Modern UI** - Beautiful, intuitive web interface with real-time monitoring
- ✅ **Simple deployment** - No dependency hell, works out of the box
- ✅ **Better debugging** - Clear error messages and easy troubleshooting
- ✅ **Flexible execution** - Local development, cloud deployment, hybrid workflows
- ✅ **Type safety** - Built-in data validation and type checking

## 🔒 Security Features

### Infrastructure Security
- ✅ **No SSH Access** - Instances accessible only via AWS Systems Manager
- ✅ **Encrypted Storage** - All EBS volumes encrypted at rest
- ✅ **Restrictive Security Groups** - Minimal network exposure
- ✅ **IAM Least Privilege** - Role-based access with minimal permissions
- ✅ **Private Networking** - No public IP addresses
- ✅ **Firewall Protection** - UFW enabled with secure defaults

### Application Security
- ✅ **Localhost Binding** - Prefect UI only accessible locally
- ✅ **Authentication Ready** - Configurable access controls
- ✅ **Secure Configuration** - Hardened settings
- ✅ **Service Isolation** - Dedicated user accounts
- ✅ **Automatic Updates** - Security patches applied automatically

## 🏗️ Provisioned Infrastructure

Terraform provisions the following **secure** resources on AWS:

### 1. EC2 Instance (`aws_instance.prefect_vm`)
- **Type:** `t3.micro` (optimized for data workloads)
- **AMI:** Ubuntu Server 22.04 LTS (dynamically selected)
- **Security:** No SSH keys, encrypted storage, restrictive security group
- **Access:** AWS Systems Manager Session Manager only
- **Purpose:** Host for Prefect server, Python scripts, and data processing tools

### 2. Security Group (`aws_security_group.prefect_sg`)
- **Ingress:** Port 4200 for Prefect UI (configurable)
- **Egress:** HTTP/HTTPS for package installation, DNS resolution
- **Purpose:** Network-level security for EC2 instance

### 3. IAM Role and Policies
- **Role:** `prefect-ec2-role` with least privilege access
- **S3 Policy:** Access only to specific datalake bucket
- **SSM Policy:** Systems Manager access for secure connections
- **Purpose:** Secure credential management

### 4. S3 Bucket (`data.aws_s3_bucket.datalake`)
- **Name:** `datalake-bucket-for-prefect-and-delta-v2`
- **Access:** Restricted to EC2 instance IAM role only
- **Purpose:** Primary datalake storage for raw data, processed data, and Delta Lake tables

### 5. CloudWatch Log Group
- **Name:** `/aws/ec2/prefect`
- **Retention:** 30 days
- **Purpose:** Centralized logging and monitoring

## ⚙️ Automation and Deployment

### GitHub Actions Workflow

The automated pipeline (`/.github/workflows/terraform.yaml`) executes:

1. **Resource Cleanup:** Removes old instances to optimize costs
2. **Security Validation:** Validates Terraform security configurations
3. **Infrastructure Provisioning:** Applies secure infrastructure on AWS
4. **Security Outputs:** Displays secure access instructions

**Triggers:**
- Push to `main` branch (only files in `/terraform/`)
- Pull Requests to `main`

### Credentials Configuration

Configure the following GitHub Secrets with **least privilege** AWS credentials:
- `AWS_ACCESS_KEY_ID`: AWS access key (with EC2, S3, IAM permissions)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## 📁 Project Structure

```
├── terraform/                 # Infrastructure as code (security-hardened)
│   ├── main.tf               # Main resources with security configurations
│   ├── variables.tf          # Terraform variables
│   └── outputs.tf            # Secure resource outputs
├── flows/                    # 🌊 Prefect flows (shared dev/prod)
│   ├── examples/             # Example data pipelines
│   ├── etl/                  # ETL workflows
│   ├── ml/                   # Machine learning pipelines
│   └── monitoring/           # Data quality and monitoring flows
├── scripts/                  # Secure configuration scripts
│   ├── install_prefect.sh    # Hardened Prefect installation
│   └── delta_lake_examples/  # Delta Lake usage examples
├── docker/                   # 🐳 Local development environment
│   ├── Dockerfile            # Prefect development container
│   ├── docker-compose.yml    # Local Prefect stack
│   └── flows/               # → Symlink to ../flows/
├── .github/workflows/        # CI/CD pipelines
│   └── terraform.yaml        # Main workflow with security checks
├── SECURITY.md              # Comprehensive security documentation
├── index.html               # Project page (GitHub Pages)
└── .gitignore              # Comprehensive ignore file for security
```

## 🛠️ Development Workflow

### 🏠 Local Development (Recommended)

1. **Start local Prefect environment:**
```bash
cd docker/
./test-prefect.sh
```

2. **Access local Prefect UI:**
```
http://localhost:4200
```

3. **Develop flows in `flows/` directory:**
```python
# flows/examples/my_pipeline.py
from prefect import flow, task

@task
def extract_data():
    return {"data": "example"}

@flow
def my_pipeline():
    data = extract_data()
    return data
```

4. **Test flows locally:**
```bash
cd flows/examples/
python my_pipeline.py
```

### ☁️ Cloud Deployment

1. **Deploy infrastructure:**
```bash
# Automatic via GitHub Actions when pushing to main
git add flows/ terraform/
git commit -m "Add new pipeline"
git push origin main
```

2. **Access cloud Prefect:**
```bash
# Port forward from EC2 instance
aws ssm start-session \
    --target <INSTANCE_ID> \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["4200"],"localPortNumber":["4200"]}'
```

3. **Deploy flows to cloud:**
```bash
# Connect to instance
aws ssm start-session --target <INSTANCE_ID>

# Deploy flows
cd /home/prefect
source prefect-env/bin/activate
python flows/examples/my_pipeline.py
```

## 🚀 Quick Start

### 1. Infrastructure Deployment
```bash
# Clone repository
git clone https://github.com/zehroque21/datalake.git
cd datalake

# Deploy infrastructure (automatic via GitHub Actions)
git push origin main
```

### 2. Local Development Setup
```bash
# Start local Prefect environment
cd docker/
./test-prefect.sh

# Access UI at http://localhost:4200
```

### 3. Secure Cloud Access

**⚠️ IMPORTANT: No SSH access is available for security reasons.**

Use AWS Systems Manager Session Manager for secure access:

```bash
# Install and configure AWS CLI
aws configure

# Start secure session
aws ssm start-session --target <INSTANCE_ID>

# Port forward Prefect UI
aws ssm start-session \
    --target <INSTANCE_ID> \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["4200"],"localPortNumber":["4200"]}'
```

### 4. Delta Lake Usage
```python
# Write example
python scripts/delta_lake_examples/write_delta_table.py

# Read example
python scripts/delta_lake_examples/read_delta_table.py
```

## 🔧 Technologies Used

- **Infrastructure:** Terraform, AWS (EC2, S3, IAM, Systems Manager)
- **Orchestration:** 🌊 Prefect (modern Python-first workflow engine)
- **Storage:** Delta Lake, AWS S3 (encrypted)
- **Processing:** Python, Apache Spark
- **Development:** Docker, Docker Compose
- **CI/CD:** GitHub Actions (with security validations)
- **Monitoring:** AWS CloudWatch, Prefect UI
- **Security:** AWS Systems Manager, IAM, Security Groups, EBS Encryption

## 📊 Solution Architecture

```
GitHub Actions → Terraform → AWS EC2 (Prefect) → AWS S3 (Encrypted Delta Lake)
                     ↓
            AWS Systems Manager (Secure Access)
                     ↓
            Local Development (Docker + Prefect)
```

1. **🏠 Local Development:** Develop and test flows using Docker + Prefect
2. **☁️ Cloud Deployment:** Deploy flows to production Prefect instance
3. **🔒 Secure Processing:** Execute workflows in hardened AWS environment
4. **📊 Encrypted Storage:** Store results in Delta Lake with encryption
5. **📈 Monitoring:** Track execution via Prefect UI and CloudWatch

## 🎯 Use Cases

- **🔄 Modern ETL/ELT Pipelines:** Python-first data processing workflows
- **🏢 Secure Data Warehousing:** Structured storage meeting compliance requirements
- **⚡ Real-time Analytics:** Stream data processing with modern orchestration
- **🤖 Machine Learning Pipelines:** End-to-end ML workflows with data lineage
- **📊 Business Intelligence:** Automated reporting and dashboard updates
- **🔍 Data Quality Monitoring:** Automated data validation and alerting

## 🌊 Prefect Flow Examples

### Basic ETL Pipeline
```python
from prefect import flow, task
import pandas as pd

@task
def extract_data(source: str):
    # Extract data from source
    return pd.read_csv(source)

@task
def transform_data(df: pd.DataFrame):
    # Transform data
    return df.dropna()

@task
def load_data(df: pd.DataFrame, destination: str):
    # Load to destination
    df.to_parquet(destination)

@flow
def etl_pipeline(source: str, destination: str):
    raw_data = extract_data(source)
    clean_data = transform_data(raw_data)
    load_data(clean_data, destination)
```

### Scheduled Data Pipeline
```python
from prefect import flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

@flow
def daily_report():
    # Your daily data processing logic
    pass

# Schedule to run daily at 6 AM
deployment = Deployment.build_from_flow(
    flow=daily_report,
    name="daily-report",
    schedule=CronSchedule(cron="0 6 * * *")
)
```

## 🔒 Security Compliance

This infrastructure follows:
- **AWS Well-Architected Framework** - Security Pillar
- **NIST Cybersecurity Framework**
- **CIS Controls** for AWS
- **OWASP Top 10** for application security

## 👨‍💻 About the Creator

**Amado Roque** - Data Engineer specialized in modern data orchestration and secure analytics solutions.

- 🔗 [LinkedIn](https://www.linkedin.com/in/amado-roque/)
- 🐙 [GitHub](https://github.com/zehroque21)

---

## 📄 License

This project is under the MIT license. See the [LICENSE](LICENSE) file for more details.

## 🤝 Contributions

Contributions are welcome! Please read our [Security Policy](SECURITY.md) before contributing.

## ⚠️ Security Notice

This infrastructure is designed with security as the top priority. Please:
- Read the [Security Policy](SECURITY.md) before deployment
- Never commit secrets or credentials to the repository
- Use only the provided secure access methods
- Report security issues responsibly

---

**[🌐 Visit the project page](https://zehroque21.github.io/datalake/)** for more information and visual documentation.

**[🔒 Read Security Policy](SECURITY.md)** for comprehensive security guidelines.

