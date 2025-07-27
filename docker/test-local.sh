#!/bin/bash

# Script para testar instalação do Airflow localmente
# Simula exatamente o que acontece na EC2

echo "🐳 Iniciando teste local do Airflow..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    error "Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    error "Execute este script do diretório docker/"
    exit 1
fi

log "Construindo imagem Docker..."
docker compose build

log "Iniciando container..."
docker compose up -d

log "Aguardando container inicializar..."
sleep 3

log "Executando instalação do Airflow..."
docker compose exec airflow-test bash -c "
    echo '🚀 Iniciando instalação do Airflow no container...'
    cd /tmp
    ./install_airflow.sh 2>&1 | tee /var/log/airflow-install.log
"

# Verificar resultado
if docker compose exec airflow-test bash -c "systemctl is-active airflow-webserver" > /dev/null 2>&1; then
    log "✅ Airflow instalado com sucesso!"
    log "🌐 Acesse: http://localhost:8080"
    log "👤 Usuário: admin"
    log "🔑 Senha: admin123"
    echo ""
    log "📋 Comandos úteis:"
    echo "  docker compose exec airflow-test bash  # Entrar no container"
    echo "  docker compose logs -f                 # Ver logs"
    echo "  docker compose down                    # Parar container"
else
    error "❌ Instalação falhou!"
    warn "📋 Para debugar:"
    echo "  docker compose exec airflow-test bash"
    echo "  tail -f /var/log/airflow-install.log"
fi

