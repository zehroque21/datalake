# 🌊 Prefect Data Orchestration Environment

Este ambiente Docker permite testar o Prefect localmente para orquestração de pipelines de dados.

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
./test-prefect.sh

# Acessar Prefect UI
# URL: http://localhost:4200
```

### Comandos Manuais

```bash
# Construir e iniciar
docker compose build
docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f prefect-server
docker compose logs -f prefect-agent

# Parar e limpar
docker compose down
```

## 📋 Arquivos

- **`Dockerfile`** - Imagem Python com Prefect
- **`docker-compose.yml`** - Prefect server + agent
- **`flows/`** - Exemplos de pipelines de dados
- **`test-prefect.sh`** - Script automatizado de teste
- **`prefect-entrypoint.sh`** - Script de inicialização

## 🧪 Exemplos de Flows

### 1. Pipeline Básico de ETL
```python
# flows/example_data_pipeline.py
@flow
def data_lake_etl():
    raw_data = extract_sample_data()
    clean_data = transform_data(raw_data)
    load_result = load_data_to_lake(clean_data)
    return load_result
```

### 2. Integração AWS
```python
# flows/aws_integration_example.py
@flow
def aws_data_lake_flow():
    buckets = list_s3_buckets()
    s3_result = simulate_s3_upload(data)
    lambda_result = trigger_lambda_function(s3_result)
    return catalog_entry
```

## 🎯 Testando Flows

### Via Interface Web
1. Acesse http://localhost:4200
2. Vá para "Deployments"
3. Execute os flows disponíveis

### Via Linha de Comando
```bash
# Entrar no container
docker compose exec prefect-server bash

# Executar flow diretamente
python /app/flows/example_data_pipeline.py

# Criar deployment
prefect deployment build /app/flows/example_data_pipeline.py:data_lake_etl -n "etl-deployment"
prefect deployment apply data_lake_etl-deployment.yaml

# Executar deployment
prefect deployment run 'data_lake_etl/etl-deployment'
```

## 🔧 Configuração

### Variáveis de Ambiente
```bash
PREFECT_API_URL=http://localhost:4200/api
PREFECT_SERVER_API_HOST=0.0.0.0
PREFECT_SERVER_API_PORT=4200
```

### Volumes
- `prefect_data:/app/.prefect` - Dados do Prefect
- `./flows:/app/flows` - Flows locais (desenvolvimento)

## 📊 Interface Web

### Dashboard Principal
- **URL:** http://localhost:4200
- **Flows:** Visualizar e executar pipelines
- **Runs:** Histórico de execuções
- **Logs:** Logs detalhados em tempo real
- **Work Pools:** Gerenciamento de workers

### Recursos da UI
- ✅ **Flow Runs** - Execuções em tempo real
- ✅ **Logs Streaming** - Logs ao vivo
- ✅ **Task Dependencies** - Visualização de DAG
- ✅ **Scheduling** - Agendamento de flows
- ✅ **Notifications** - Alertas e notificações

## 🎯 Vantagens do Prefect

### vs Airflow
- ✅ **Instalação simples** - Sem dependency hell
- ✅ **UI moderna** - Interface mais intuitiva
- ✅ **Python-first** - Código mais limpo
- ✅ **Debugging fácil** - Logs claros e estruturados
- ✅ **Desenvolvimento local** - Execução sem servidor

### Recursos Avançados
- 🔄 **Retry automático** com backoff
- 📊 **Observabilidade** completa
- 🔒 **Secrets management** integrado
- ☁️ **Cloud-native** por design
- 🚀 **Deployment flexível**

## 🚀 Próximos Passos

Após testar localmente:
1. ✅ **Validar interface** e usabilidade
2. ✅ **Testar flows** de exemplo
3. ✅ **Criar pipelines** customizados
4. ✅ **Deploy na AWS** se aprovado

## 🐛 Troubleshooting

### Problemas Comuns
```bash
# Prefect server não inicia
docker compose logs prefect-server

# Agent não conecta
docker compose logs prefect-agent

# Porta 4200 ocupada
docker compose down && docker compose up -d

# Reset completo
docker compose down -v && docker compose up -d
```

### Comandos de Debug
```bash
# Status dos containers
docker compose ps

# Logs em tempo real
docker compose logs -f

# Entrar no container
docker compose exec prefect-server bash

# Verificar conectividade
curl http://localhost:4200/api/health
```

