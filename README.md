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

# DataLake AWS - Plataforma de Engenharia de Dados Moderna

> Solução completa, segura e automatizada para Data Lake na AWS, com orquestração Prefect, Delta Lake e infraestrutura como código.

🌐 [Página do projeto](https://zehroque21.github.io/datalake/) • 🔒 [Política de Segurança](SECURITY.md)

---

## Visão Geral

- Infraestrutura provisionada via Terraform (EC2, S3, IAM, Security Groups)
- Orquestração de pipelines com Prefect (Python-first, UI moderna)
- Armazenamento transacional com Delta Lake (S3)
- Segurança: sem SSH, acesso só via AWS SSM, storage criptografado, IAM mínimo
- CI/CD automatizado com GitHub Actions

## Como usar

### 1. Deploy da Infraestrutura (automático)

```bash
git clone https://github.com/zehroque21/datalake.git
cd datalake
git push origin main  # Terraform roda via GitHub Actions
```

### 2. Ambiente Local (Prefect)

```bash
cd docker/
./test-prefect.sh
# Acesse http://localhost:4200
```

### 3. Desenvolva e teste pipelines

```python
from prefect import flow, task

@task
def extract():
    return "dados"

@flow
def pipeline():
    d = extract()
    return d
```

### 4. Acesso seguro à nuvem

```bash
aws configure
aws ssm start-session --target <INSTANCE_ID>
# Port forward Prefect UI
aws ssm start-session --target <INSTANCE_ID> \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["4200"],"localPortNumber":["4200"]}'
```

### 5. Exemplo Delta Lake

```bash
python scripts/delta_lake_examples/write_delta_table.py
python scripts/delta_lake_examples/read_delta_table.py
```

## Estrutura do Projeto

```
├── terraform/         # Infraestrutura como código
├── scripts/           # Scripts e exemplos Delta Lake
├── docker/            # Ambiente local Prefect
├── .github/           # CI/CD
├── index.html         # Página do projeto
```

## Tecnologias

- Terraform, AWS (EC2, S3, IAM, SSM)
- Prefect, Delta Lake, Python, Docker
- GitHub Actions, CloudWatch

## Sobre

**Amado Roque** — Data Engineer

[LinkedIn](https://www.linkedin.com/in/amado-roque/) • [GitHub](https://github.com/zehroque21)

---

MIT License • [Política de Segurança](SECURITY.md)
### 🏠 Local Development (Recommended)


