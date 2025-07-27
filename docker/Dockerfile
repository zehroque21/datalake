# Dockerfile para testar ambiente Airflow localmente
# Replica exatamente o ambiente EC2 Ubuntu 22.04

FROM ubuntu:22.04

# Evitar prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Instalar dependências básicas (igual à EC2)
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        net-tools \
        curl \
        wget \
        git \
        sudo \
        systemctl \
        cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Criar usuário airflow (igual à EC2)
RUN useradd -m -s /bin/bash airflow && \
    usermod -aG sudo airflow && \
    echo "airflow ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Criar diretórios necessários
RUN mkdir -p /var/log && \
    touch /var/log/airflow-install.log && \
    chown airflow:airflow /var/log/airflow-install.log

# Copiar script de instalação
COPY scripts/install_airflow.sh /tmp/install_airflow.sh
RUN chmod +x /tmp/install_airflow.sh

# Expor porta do Airflow
EXPOSE 8080

# Comando padrão
CMD ["/bin/bash"]

