#!/bin/bash

# DataLake - Script de Inicialização
# Versão Nativa Simples e Eficiente

set -e

echo "🌊 DataLake - Inicializando..."
echo "=============================="

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Inicie o Docker Desktop primeiro."
    exit 1
fi

# Ir para diretório do script
cd "$(dirname "$0")"

echo "📁 Diretório atual: $(pwd)"

# Parar containers existentes (se houver)
echo "🛑 Parando containers existentes..."
docker compose down 2>/dev/null || true

# Limpar volumes se solicitado
if [ "$1" = "--clean" ]; then
    echo "🧹 Limpando volumes..."
    docker compose down -v
    docker volume prune -f
fi

# Build da imagem
echo "🔨 Construindo imagem..."
docker compose build

# Iniciar serviços
echo "🚀 Iniciando DataLake..."
docker compose up -d

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 10

# Verificar status
echo "📊 Status dos serviços:"
docker compose ps

# Verificar se app está respondendo
echo "🔍 Testando conectividade..."
for i in {1..30}; do
    if curl -s http://localhost:5420/api/metrics > /dev/null; then
        echo "✅ Aplicação iniciada com sucesso!"
        break
    fi
    echo "   Tentativa $i/30 - aguardando..."
    sleep 2
done

# URLs de acesso
echo ""
echo "🎉 DataLake está rodando!"
echo "========================"
echo "📊 Dashboard: http://localhost:5420"
echo "🔧 API Métricas: http://localhost:5420/api/metrics"
echo "🌡️ API Weather: http://localhost:5420/api/weather"
echo "📋 API Jobs: http://localhost:5420/api/jobs"
echo ""
echo "💡 Comandos úteis:"
echo "   Ver logs: docker compose logs -f"
echo "   Parar: docker compose down"
echo "   Reiniciar: ./start-datalake.sh"
echo "   Reset completo: ./start-datalake.sh --clean"
echo ""
echo "🔄 O job de coleta roda automaticamente a cada 30 minutos"
echo "▶️ Use o botão 'Executar Job' no dashboard para teste manual"

