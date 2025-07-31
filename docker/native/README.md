# 🌊 DataLake Native - Versão Simples

Uma implementação leve e nativa de um data lake com Flask, jobs agendados e dashboard interativo.

## 🎯 **Objetivo**

Esta é uma versão simplificada para:
- ✅ **Aprendizado** - Entender conceitos sem complexidade
- ✅ **Desenvolvimento local** - Teste rápido e iteração
- ✅ **Free tier AWS** - Recursos mínimos necessários
- ✅ **Base evolutiva** - Fundação para crescer

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

## 🚀 **Como Usar**

### **Iniciar Local:**
```bash
cd docker/native/
./start-native.sh
```

### **Acessar:**
- **Dashboard:** http://localhost:5000
- **API:** http://localhost:5000/api/metrics

### **Parar:**
```bash
docker compose -f docker-compose-native.yml down
```

### **Reset Completo:**
```bash
./start-native.sh --clean
```

## 📊 **Funcionalidades**

### **✅ Implementado:**
- 🌡️ **Job de coleta** - Dados meteorológicos a cada 30min
- 📊 **Dashboard** - Métricas, gráficos, tabelas
- 🔄 **Scheduler** - Jobs automáticos com APScheduler
- 📋 **API REST** - Endpoints para dados e métricas
- 💾 **Persistência** - SQLite com SQLAlchemy
- 📈 **Visualização** - Chart.js para gráficos
- ⚡ **Responsivo** - Tailwind CSS + Alpine.js

### **🔄 Jobs Automáticos:**
- **weather_collection** - Coleta temperatura de Campinas
- **Frequência:** A cada 30 minutos
- **Trigger manual:** Botão no dashboard

### **📊 Métricas Disponíveis:**
- Total de jobs executados
- Taxa de sucesso/falha
- Jobs executados hoje
- Última execução
- Histórico completo

## 🛠️ **Stack Técnica**

### **Backend:**
- **Flask** - Web framework
- **SQLAlchemy** - ORM/Database
- **APScheduler** - Jobs agendados
- **Pandas** - Processamento de dados
- **Gunicorn** - WSGI server

### **Frontend:**
- **Chart.js** - Gráficos interativos
- **Alpine.js** - Reatividade leve
- **Tailwind CSS** - Styling moderno
- **Vanilla JS** - Sem frameworks pesados

### **Infraestrutura:**
- **Docker** - Containerização
- **SQLite** - Database local
- **PostgreSQL** - Opção para produção

## 📁 **Estrutura de Arquivos**

```
native/
├── app/
│   ├── app.py              # Flask app principal
│   ├── templates/
│   │   └── dashboard.html  # Dashboard UI
│   ├── static/             # Assets estáticos
│   ├── jobs/               # Jobs agendados (futuro)
│   └── models/             # Models SQLAlchemy (futuro)
├── docker-compose-native.yml
├── Dockerfile-native
├── requirements.txt
├── start-native.sh
└── README.md
```

## 🔧 **Configuração**

### **Variáveis de Ambiente:**
```bash
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///data/datalake.db
```

### **Recursos Necessários:**
- **RAM:** ~200MB
- **CPU:** Mínimo
- **Storage:** ~50MB
- **Portas:** 5000

## 🚀 **Evolução Planejada**

### **Fase 2 - Mais Jobs:**
- Múltiplas fontes de dados
- Jobs com diferentes frequências
- Processamento com pandas avançado

### **Fase 3 - Dashboard Avançado:**
- Mais gráficos e métricas
- Filtros e drill-down
- Alertas e notificações

### **Fase 4 - Deploy AWS:**
- PostgreSQL RDS
- EC2 otimizado
- Monitoramento CloudWatch

## 🐛 **Troubleshooting**

### **App não inicia:**
```bash
# Ver logs
docker compose -f docker-compose-native.yml logs -f

# Verificar porta
netstat -tlnp | grep 5000
```

### **Jobs não executam:**
```bash
# Trigger manual via API
curl http://localhost:5000/api/jobs/trigger/weather_collection

# Verificar logs do scheduler
docker compose -f docker-compose-native.yml logs datalake-native
```

### **Dashboard não carrega dados:**
```bash
# Testar APIs
curl http://localhost:5000/api/metrics
curl http://localhost:5000/api/weather
curl http://localhost:5000/api/jobs
```

## 💡 **Próximos Passos**

1. **Teste local** - Execute e explore o dashboard
2. **Customize jobs** - Adicione suas próprias fontes de dados
3. **Evolua UI** - Melhore o dashboard conforme necessidade
4. **Deploy AWS** - Quando estiver satisfeito com funcionalidades

---

**🎯 Esta é sua base para um data lake moderno e eficiente!**

