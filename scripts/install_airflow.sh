#!/bin/bash

# Script para instalar o Apache Airflow em uma instância EC2

# Atualizar o sistema
sudo apt-get update -y
sudo apt-get upgrade -y

# Instalar Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Adicionar o usuário atual ao grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Criar diretórios para o Airflow
mkdir -p ~/airflow/dags ~/airflow/logs ~/airflow/plugins

# Baixar o docker-compose.yaml do Airflow
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.7.0/docker-compose.yaml'
mv docker-compose.yaml ~/airflow/

# Inicializar o banco de dados do Airflow
cd ~/airflow
docker compose up airflow-init

# Iniciar o Airflow
docker compose up -d

echo "Airflow instalado e rodando! Acesse o Airflow UI no IP público da sua VM na porta 8080."


