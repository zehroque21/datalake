# 🐳 Ambiente de Teste Local do Airflow

Este ambiente Docker permite testar a instalação do Airflow localmente antes do deploy na AWS.

## 🚀 Como Usar

### Pré-requisitos
- Docker Desktop instalado e rodando
- Git para clonar o repositório

### Comandos Básicos

```bash
# Clonar repositório
git clone https://github.com/zehroque21/datalake.git
cd datalake/docker

# Executar teste automatizado
./test-local.sh

# Acessar Airflow
# URL: http://localhost:8080
# Usuário: admin
# Senha: admin123
```

### Debug Manual

```bash
# Entrar no container
docker compose exec airflow-test bash

# Ver logs de instalação
tail -f /var/log/airflow-install.log

# Ver logs do Airflow
tail -f /home/airflow/airflow-webserver.log
tail -f /home/airflow/airflow-scheduler.log

# Parar e limpar
docker compose down
```

## 📋 Arquivos

- **`Dockerfile`** - Imagem Ubuntu 22.04 com Airflow
- **`docker-compose.yml`** - Configuração do container
- **`install_airflow.sh`** - Script de instalação que funciona
- **`test-local.sh`** - Script automatizado de teste
- **`.dockerignore`** - Otimização do build

## ✅ Versão Testada

- **Airflow:** 2.8.1 (instalação minimal sem providers)
- **Python:** 3.10
- **Executor:** SequentialExecutor
- **Database:** SQLite

## 🎯 Próximos Passos

Após confirmar que funciona localmente:
1. Adaptar script para infraestrutura EC2
2. Adicionar providers necessários
3. Deploy na AWS com confiança

