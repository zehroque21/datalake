# DataLake AWS - Plataforma de Engenharia de Dados

🌐 **[Acesse a página do projeto](https://zehroque21.github.io/datalake/)** para uma visão completa da solução.

---

Este repositório contém uma solução completa de datalake que combina as melhores práticas de engenharia de dados com infraestrutura como código (IaC). A plataforma oferece um ambiente robusto para processamento e análise de dados em escala, utilizando Apache Airflow para orquestração e Delta Lake para armazenamento confiável.

## 🚀 Visão Geral

A solução provisiona automaticamente uma infraestrutura moderna de datalake na Amazon Web Services (AWS), integrando:

- **Apache Airflow** para orquestração de pipelines de dados
- **Delta Lake** para armazenamento transacional e versionado
- **AWS S3** para storage escalável e durável
- **EC2** otimizada para processamento de dados
- **CI/CD** integrado via GitHub Actions

## 🏗️ Infraestrutura Provisionada

O Terraform provisiona os seguintes recursos na AWS:

### 1. Instância EC2 (`aws_instance.airflow_vm`)
- **Tipo:** `t3.micro` (otimizada para cargas de trabalho de dados)
- **AMI:** Ubuntu Server 22.04 LTS (selecionada dinamicamente)
- **Finalidade:** Host para Apache Airflow, scripts Python, Spark e outras ferramentas de processamento

### 2. Bucket S3 (`data.aws_s3_bucket.datalake`)
- **Nome:** `datalake-bucket-for-airflow-and-delta-v2`
- **Finalidade:** Armazenamento principal do datalake para dados brutos, processados e tabelas Delta Lake

## ⚙️ Automação e Deploy

### GitHub Actions Workflow

O pipeline automatizado (`/.github/workflows/terraform.yaml`) executa:

1. **Limpeza de Recursos:** Remove instâncias antigas para otimizar custos
2. **Validação:** Formata, valida e planeja mudanças no Terraform
3. **Provisionamento:** Aplica a infraestrutura na AWS
4. **Outputs:** Exibe informações dos recursos criados

**Triggers:**
- Push para branch `main` (apenas arquivos em `/terraform/`)
- Pull Requests para `main`

### Configuração de Credenciais

Configure os seguintes GitHub Secrets:
- `AWS_ACCESS_KEY_ID`: Chave de acesso AWS
- `AWS_SECRET_ACCESS_KEY`: Chave secreta AWS

## 📁 Estrutura do Projeto

```
├── terraform/                 # Infraestrutura como código
│   ├── main.tf               # Recursos principais (EC2, S3)
│   ├── variables.tf          # Variáveis do Terraform
│   └── outputs.tf            # Outputs dos recursos
├── scripts/                  # Scripts de configuração e exemplos
│   ├── install_airflow.sh    # Instalação do Apache Airflow
│   └── delta_lake_examples/  # Exemplos de uso do Delta Lake
│       ├── write_delta_table.py
│       └── read_delta_table.py
├── .github/workflows/        # Pipelines CI/CD
│   └── terraform.yaml        # Workflow principal
└── index.html               # Página do projeto (GitHub Pages)
```

## 🛠️ Configuração e Uso

### 1. Deploy da Infraestrutura
```bash
# O deploy é automático via GitHub Actions
# Faça push de alterações em /terraform/ para disparar
git add terraform/
git commit -m "Update infrastructure"
git push origin main
```

### 2. Acesso à Instância EC2
```bash
# Conecte-se via SSH (configure sua chave SSH na AWS)
ssh -i sua-chave.pem ubuntu@<IP_PUBLICO_EC2>
```

### 3. Instalação do Airflow
```bash
# Na instância EC2, execute:
cd /path/to/repository
bash scripts/install_airflow.sh
```

### 4. Uso do Delta Lake
```python
# Exemplo de escrita
python scripts/delta_lake_examples/write_delta_table.py

# Exemplo de leitura
python scripts/delta_lake_examples/read_delta_table.py
```

## 🔧 Tecnologias Utilizadas

- **Infraestrutura:** Terraform, AWS (EC2, S3, IAM)
- **Orquestração:** Apache Airflow
- **Armazenamento:** Delta Lake, AWS S3
- **Processamento:** Python, Apache Spark
- **CI/CD:** GitHub Actions
- **Monitoramento:** Airflow Web UI

## 📊 Arquitetura da Solução

```
GitHub Actions → Terraform → AWS EC2 (Airflow) → AWS S3 (Delta Lake)
```

1. **Ingestão:** Coleta de dados via pipelines Airflow
2. **Processamento:** Transformações com Python/Spark
3. **Armazenamento:** Dados salvos em formato Delta Lake
4. **Análise:** Consultas e analytics sobre os dados processados

## 🎯 Casos de Uso

- **ETL/ELT Pipelines:** Processamento automatizado de dados
- **Data Warehousing:** Armazenamento estruturado para analytics
- **Real-time Analytics:** Processamento de streams de dados
- **Machine Learning:** Preparação de dados para modelos ML
- **Business Intelligence:** Dashboards e relatórios

## 👨‍💻 Sobre o Criador

**Amado Roque** - Engenheiro de Dados especializado em soluções de big data e analytics.

- 🔗 [LinkedIn](https://www.linkedin.com/in/amado-roque/)
- 🐙 [GitHub](https://github.com/zehroque21)

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

---

**[🌐 Visite a página do projeto](https://zehroque21.github.io/datalake/)** para mais informações e documentação visual.

