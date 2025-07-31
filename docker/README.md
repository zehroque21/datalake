# 🌊 DataLake - Versão Nativa e Eficiente

Uma implementação moderna e leve de um data lake com Flask, jobs agendados e dashboard interativo.

## 🎯 **Características**

- ✅ **Leve e Rápido** - Apenas ~200MB RAM
- ✅ **Fácil de Usar** - Um comando para iniciar
- ✅ **Moderno** - Flask + SQLAlchemy + Chart.js
- ✅ **Responsivo** - Interface mobile-friendly
- ✅ **Evolutivo** - Base sólida para crescer
- ✅ **AWS Ready** - Perfeito para free tier

## 🚀 **Início Rápido**

```bash
# Clonar repositório
git clone https://github.com/zehroque21/datalake
cd datalake/docker/

# Iniciar DataLake
./start-datalake.sh

# Acessar dashboard
open http://localhost:5420
```

## 🏗️ **Arquitetura**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Flask API     │    │   Scheduler     │
│   (HTML/JS)     │◄──►│   (Python)      │◄──►│   (APScheduler) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │   (Dados)       │
                       └─────────────────┘
```

## 📊 **Funcionalidades**

### **🔄 Jobs Automáticos**
- **Coleta meteorológica** - Dados de Campinas a cada 30min
- **Scheduler robusto** - APScheduler com persistência
- **Trigger manual** - Execução sob demanda via dashboard
- **Monitoramento** - Logs e métricas de execução

### **📈 Dashboard Interativo**
- **Métricas em tempo real** - Jobs, sucessos, falhas
- **Gráficos dinâmicos** - Chart.js com dados históricos
- **Tabelas responsivas** - Histórico de execuções
- **Auto-refresh** - Atualização automática a cada 30s

### **🔌 APIs REST**
- `GET /api/metrics` - Métricas gerais do sistema
- `GET /api/weather` - Dados meteorológicos coletados
- `GET /api/jobs` - Histórico de execuções de jobs
- `POST /api/jobs/trigger/<job>` - Executar job manualmente

## 🛠️ **Stack Técnica**

### **Backend**
- **Flask 3.0** - Web framework moderno
- **SQLAlchemy** - ORM com SQLite/PostgreSQL
- **APScheduler** - Jobs agendados robustos
- **Pandas** - Processamento de dados
- **Gunicorn** - WSGI server para produção

### **Frontend**
- **Chart.js** - Gráficos interativos (~200KB)
- **Alpine.js** - Reatividade leve (~15KB)
- **Tailwind CSS** - Styling moderno (~10KB)
- **Vanilla JS** - Sem frameworks pesados

## 📁 **Estrutura do Projeto**

```
docker/
├── app/
│   ├── app.py              # Aplicação Flask principal
│   └── templates/
│       └── dashboard.html  # Interface do dashboard
├── docker-compose.yml      # Orquestração de containers
├── Dockerfile              # Imagem Docker otimizada
├── requirements.txt        # Dependências Python
├── start-datalake.sh       # Script de inicialização
└── README.md              # Esta documentação
```

## ⚙️ **Configuração**

### **Variáveis de Ambiente**
```bash
FLASK_ENV=development       # Modo de desenvolvimento
FLASK_DEBUG=1              # Debug ativo
DATABASE_URL=sqlite:///data/datalake.db  # Database local
```

### **Recursos Necessários**
- **RAM:** ~200MB (perfeito para AWS free tier)
- **CPU:** Mínimo (1 vCPU suficiente)
- **Storage:** ~50MB
- **Porta:** 5420

## 🔧 **Comandos Úteis**

```bash
# Iniciar aplicação
./start-datalake.sh

# Ver logs em tempo real
docker compose logs -f

# Parar aplicação
docker compose down

# Reset completo (limpa dados)
./start-datalake.sh --clean

# Executar job manualmente
curl -X POST http://localhost:5420/api/jobs/trigger/weather_collection
```

## 📊 **Monitoramento**

### **Métricas Disponíveis**
- Total de jobs executados
- Taxa de sucesso/falha
- Jobs executados hoje
- Duração média de execução
- Última execução e status

### **Logs Estruturados**
```bash
# Ver logs da aplicação
docker compose logs datalake

# Filtrar por nível
docker compose logs datalake | grep ERROR
docker compose logs datalake | grep INFO
```

## 🚀 **Deploy em Produção**

### **AWS EC2 (Free Tier)**
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clonar e iniciar
git clone https://github.com/zehroque21/datalake
cd datalake/docker/
./start-datalake.sh

# Configurar proxy reverso (opcional)
# nginx, traefik, ou cloudflare tunnel
```

### **PostgreSQL (Produção)**
```bash
# Ativar PostgreSQL em vez de SQLite
docker compose --profile postgres up -d

# Atualizar DATABASE_URL no docker-compose.yml
DATABASE_URL=postgresql://datalake:datalake123@postgres:5432/datalake
```

## 🔄 **Evolução Planejada**

### **Fase 2 - Mais Fontes de Dados**
- APIs de diferentes provedores
- Múltiplas cidades e regiões
- Dados financeiros e econômicos
- Integração com webhooks

### **Fase 3 - Analytics Avançados**
- Machine learning com scikit-learn
- Previsões e tendências
- Alertas automáticos
- Relatórios agendados

### **Fase 4 - Infraestrutura**
- Kubernetes deployment
- Monitoramento com Prometheus
- CI/CD com GitHub Actions
- Backup automático

## 🐛 **Troubleshooting**

### **App não inicia**
```bash
# Verificar logs
docker compose logs datalake

# Verificar porta ocupada
netstat -tlnp | grep 5420

# Rebuild completo
./start-datalake.sh --clean
```

### **Jobs não executam**
```bash
# Trigger manual
curl -X POST http://localhost:5420/api/jobs/trigger/weather_collection

# Verificar scheduler
docker compose logs datalake | grep scheduler
```

### **Dashboard não carrega**
```bash
# Testar APIs
curl http://localhost:5420/api/metrics
curl http://localhost:5420/api/weather

# Verificar JavaScript no browser console
```

## 🤝 **Contribuição**

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Add nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](../LICENSE) para detalhes.

---

**🌊 DataLake - Simples, Eficiente e Moderno**

*Construído com ❤️ para ser a base perfeita do seu data lake*

