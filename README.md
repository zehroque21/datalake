# Datalake de Aprendizado na AWS (Free Tier)

Este repositório contém a infraestrutura como código (IaC) e scripts para provisionar um ambiente de datalake de aprendizado na Amazon Web Services (AWS), utilizando os recursos do Free Tier. O objetivo é permitir a experimentação com ferramentas de engenharia de dados como Apache Airflow e Delta Lake, sem incorrer em custos.

## Infraestrutura Provisionada (via Terraform)

O Terraform é utilizado para provisionar os seguintes recursos na sua conta AWS:

1.  **Instância EC2 (`aws_instance.airflow_vm`)**:
    *   **Tipo:** `t3.micro` (elegível para o Free Tier).
    *   **AMI:** Ubuntu Server 22.04 LTS (a AMI mais recente é buscada dinamicamente para garantir compatibilidade).
    *   **Finalidade:** Esta máquina virtual servirá como host para a instalação do Apache Airflow, que será utilizado para orquestrar pipelines de dados. É um ambiente flexível para rodar scripts Python, Spark (se configurado) e outras ferramentas.

2.  **Bucket S3 (`aws_s3_bucket.datalake`)**:
    *   **Nome:** `datalake-bucket-for-airflow-and-delta-v2` (ou o nome atualizado no `main.tf`).
    *   **Finalidade:** Este bucket será o armazenamento principal do seu datalake. Ele será usado para armazenar dados brutos, dados processados e, crucialmente, as tabelas Delta Lake. O S3 é um serviço de armazenamento de objetos altamente escalável e durável, com um generoso Free Tier.

## Como Funciona

As alterações na infraestrutura são automatizadas via GitHub Actions. Quando você faz um `push` para a branch `main` (ou abre um Pull Request), um workflow do GitHub Actions é disparado para executar o Terraform.

### GitHub Actions Workflow (`.github/workflows/terraform.yaml`)

Este workflow é responsável por:

*   **Configurar Credenciais AWS:** Utiliza os `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` configurados como GitHub Secrets para autenticar na AWS.
*   **Inicializar Terraform:** Executa `terraform init` para preparar o diretório de trabalho do Terraform.
*   **Validar e Planejar:** Executa `terraform fmt` para formatar o código, `terraform validate` para verificar a sintaxe e `terraform plan` para mostrar as mudanças que serão aplicadas.
*   **Aplicar Mudanças:** Executa `terraform apply` para provisionar ou atualizar os recursos na AWS. **Este passo só é executado em `push` para a branch `main` e em Pull Requests para `main` (com aprovação manual para `apply`).**

## Scripts Adicionais

*   **`scripts/install_airflow.sh`**: Um script shell para auxiliar na instalação do Apache Airflow na instância EC2 provisionada.
*   **`scripts/delta_lake_examples/`**: Contém exemplos de scripts Python para interagir com o Delta Lake no S3, demonstrando como ler e escrever dados em formato Delta.

## Próximos Passos

1.  **Configurar GitHub Secrets:** Certifique-se de que `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` estão configurados como GitHub Secrets no seu repositório, com as permissões IAM adequadas para criar EC2 e S3.
2.  **Acompanhar o Deploy:** Monitore o progresso do workflow do GitHub Actions na aba "Actions" do seu repositório.
3.  **Acessar a VM:** Após o deploy bem-sucedido, você poderá acessar a instância EC2 via SSH (utilizando a chave SSH que você associar à instância, se configurado no Terraform, ou criando uma manualmente).
4.  **Instalar Airflow:** Execute o script `install_airflow.sh` na VM para configurar o Apache Airflow.
5.  **Experimentar Delta Lake:** Utilize os scripts de exemplo do Delta Lake para começar a trabalhar com dados no S3.

Este ambiente é projetado para aprendizado e experimentação. Lembre-se de monitorar o uso dos recursos da AWS para garantir que você permaneça dentro dos limites do Free Tier.

