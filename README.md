# DataLake AWS - Data Engineering Platform

🌐 **[Visit the project page](https://zehroque21.github.io/datalake/)** for a complete overview of the solution.

🔒 **[Security Policy](SECURITY.md)** - Read our comprehensive security guidelines.

---

This repository contains a **secure** and complete datalake solution that combines data engineering best practices with infrastructure as code (IaC). The platform provides a robust and hardened environment for data processing and analysis at scale, using Apache Airflow for orchestration and Delta Lake for reliable storage.

## 🚀 Overview

The solution automatically provisions a modern, **security-hardened** datalake infrastructure on Amazon Web Services (AWS), integrating:

- **Apache Airflow** for data pipeline orchestration
- **Delta Lake** for transactional and versioned storage
- **AWS S3** for scalable and durable storage
- **EC2** optimized and hardened for data processing
- **CI/CD** integrated via GitHub Actions
- **Security-first** approach with no SSH access

## 🔒 Security Features

### Infrastructure Security
- ✅ **No SSH Access** - Instances accessible only via AWS Systems Manager
- ✅ **Encrypted Storage** - All EBS volumes encrypted at rest
- ✅ **Restrictive Security Groups** - Minimal network exposure
- ✅ **IAM Least Privilege** - Role-based access with minimal permissions
- ✅ **Private Networking** - No public IP addresses
- ✅ **Firewall Protection** - UFW enabled with secure defaults

### Application Security
- ✅ **Localhost Binding** - Airflow UI only accessible locally
- ✅ **Authentication Required** - Password-protected access
- ✅ **Secure Configuration** - Hardened settings
- ✅ **Service Isolation** - Dedicated user accounts
- ✅ **Automatic Updates** - Security patches applied automatically

## 🏗️ Provisioned Infrastructure

Terraform provisions the following **secure** resources on AWS:

### 1. EC2 Instance (`aws_instance.airflow_vm`)
- **Type:** `t3.micro` (optimized for data workloads)
- **AMI:** Ubuntu Server 22.04 LTS (dynamically selected)
- **Security:** No SSH keys, encrypted storage, restrictive security group
- **Access:** AWS Systems Manager Session Manager only
- **Purpose:** Host for Apache Airflow, Python scripts, Spark, and other processing tools

### 2. Security Group (`aws_security_group.airflow_sg`)
- **Ingress:** No inbound rules (except optional Airflow UI from specific IP)
- **Egress:** HTTP/HTTPS for package installation, DNS resolution
- **Purpose:** Network-level security for EC2 instance

### 3. IAM Role and Policies
- **Role:** `airflow-ec2-role` with least privilege access
- **S3 Policy:** Access only to specific datalake bucket
- **SSM Policy:** Systems Manager access for secure connections
- **Purpose:** Secure credential management

### 4. S3 Bucket (`data.aws_s3_bucket.datalake`)
- **Name:** `datalake-bucket-for-airflow-and-delta-v2`
- **Access:** Restricted to EC2 instance IAM role only
- **Purpose:** Primary datalake storage for raw data, processed data, and Delta Lake tables

### 5. CloudWatch Log Group
- **Name:** `/aws/ec2/airflow`
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
├── scripts/                  # Secure configuration scripts and examples
│   ├── install_airflow.sh    # Hardened Apache Airflow installation
│   └── delta_lake_examples/  # Delta Lake usage examples
│       ├── write_delta_table.py
│       └── read_delta_table.py
├── .github/workflows/        # CI/CD pipelines
│   └── terraform.yaml        # Main workflow with security checks
├── SECURITY.md              # Comprehensive security documentation
├── index.html               # Project page (GitHub Pages)
└── .gitignore              # Comprehensive ignore file for security
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

### 2. Secure Instance Access

**⚠️ IMPORTANT: No SSH access is available for security reasons.**

Use AWS Systems Manager Session Manager for secure access:

#### Method 1: AWS CLI (Recommended)
```bash
# Install and configure AWS CLI
aws configure

# Start secure session
aws ssm start-session --target <INSTANCE_ID>
```

#### Method 2: AWS Console
1. Go to EC2 → Instances
2. Select your instance
3. Click "Connect" → "Session Manager"
4. Click "Connect"

### 3. Airflow Installation
```bash
# Once connected via Session Manager, run:
cd /home/ubuntu
git clone https://github.com/zehroque21/datalake.git
cd datalake
bash scripts/install_airflow.sh
```

### 4. Accessing Airflow Web UI

The Airflow UI is only accessible locally for security. Use port forwarding:

```bash
# Forward port 8080 from instance to local machine
aws ssm start-session \
    --target <INSTANCE_ID> \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'
```

Then access `http://localhost:8080` in your browser.

### 5. Delta Lake Usage
```python
# Write example
python scripts/delta_lake_examples/write_delta_table.py

# Read example
python scripts/delta_lake_examples/read_delta_table.py
```

## 🔧 Technologies Used

- **Infrastructure:** Terraform, AWS (EC2, S3, IAM, Systems Manager)
- **Orchestration:** Apache Airflow (security-hardened)
- **Storage:** Delta Lake, AWS S3 (encrypted)
- **Processing:** Python, Apache Spark
- **CI/CD:** GitHub Actions (with security validations)
- **Monitoring:** AWS CloudWatch
- **Security:** AWS Systems Manager, IAM, Security Groups, EBS Encryption

## 📊 Solution Architecture

```
GitHub Actions → Terraform → AWS EC2 (Hardened) → AWS S3 (Encrypted Delta Lake)
                     ↓
            AWS Systems Manager (Secure Access)
```

1. **Secure Ingestion:** Data collection via hardened Airflow pipelines
2. **Protected Processing:** Transformations with Python/Spark in isolated environment
3. **Encrypted Storage:** Data saved in Delta Lake format with encryption
4. **Monitored Analysis:** Queries and analytics with comprehensive logging

## 🎯 Use Cases

- **Secure ETL/ELT Pipelines:** Automated data processing with security controls
- **Compliant Data Warehousing:** Structured storage meeting security requirements
- **Protected Real-time Analytics:** Stream data processing with encryption
- **Secure Machine Learning:** Data preparation for ML models with access controls
- **Auditable Business Intelligence:** Dashboards and reports with full logging

## 🔒 Security Compliance

This infrastructure follows:
- **AWS Well-Architected Framework** - Security Pillar
- **NIST Cybersecurity Framework**
- **CIS Controls** for AWS
- **OWASP Top 10** for application security

## 👨‍💻 About the Creator

**Amado Roque** - Data Engineer specialized in secure big data and analytics solutions.

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

