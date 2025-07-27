# 🐳 Ambiente de Teste Local do Airflow

Este ambiente Docker replica exatamente o ambiente EC2 Ubuntu 22.04 para testar a instalação do Airflow localmente.

## 🚀 Como Usar

### Pré-requisitos
- Docker instalado e rodando
- Docker Compose instalado

### Teste Rápido
```bash
cd docker/
./test-local.sh
```

### Teste Manual
```bash
# Construir e iniciar
cd docker/
docker compose up -d

# Entrar no container
docker compose exec airflow-test bash

# Executar instalação manualmente
cd /tmp
./install_airflow.sh

# Ver logs
tail -f /var/log/airflow-install.log
```

### Acessar Airflow
- **URL:** http://localhost:8080
- **Usuário:** admin
- **Senha:** admin123

## 🔧 Comandos Úteis

```bash
# Ver logs do container
docker compose logs -f

# Reiniciar container
docker compose restart

# Parar e remover
docker compose down

# Limpar volumes (reset completo)
docker compose down -v

# Entrar no container para debug
docker compose exec airflow-test bash

# Ver status dos serviços Airflow
docker compose exec airflow-test systemctl status airflow-webserver
docker compose exec airflow-test systemctl status airflow-scheduler
```

## 🐛 Debug

### Ver logs de instalação
```bash
docker compose exec airflow-test tail -f /var/log/airflow-install.log
```

### Verificar versão instalada
```bash
docker compose exec airflow-test sudo -u airflow bash -c "
cd /home/airflow
source airflow-env/bin/activate
pip show apache-airflow | grep Version
"
```

### Testar comando airflow
```bash
docker compose exec airflow-test sudo -u airflow bash -c "
cd /home/airflow
source airflow-env/bin/activate
export AIRFLOW_HOME=/home/airflow/airflow
airflow version
"
```

## 📁 Estrutura

```
docker/
├── Dockerfile              # Imagem Ubuntu 22.04 + dependências
├── docker-compose.yml      # Configuração do container
├── test-local.sh           # Script de teste automatizado
└── README.md               # Esta documentação
```

## 🎯 Vantagens

- ✅ **Ambiente idêntico** à EC2
- ✅ **Teste rápido** (segundos vs minutos)
- ✅ **Debug fácil** com logs em tempo real
- ✅ **Sem custos** AWS
- ✅ **Iteração rápida** para correções
- ✅ **Reset simples** com `docker compose down -v`

## 🔄 Workflow Recomendado

1. **Teste local** com `./test-local.sh`
2. **Debug e correção** se necessário
3. **Commit mudanças** quando funcionar
4. **Deploy na EC2** com confiança

