#!/bin/bash

# Script para inicializar todos os índices necessários do OpenMetadata
# Este script deve ser executado após o Elasticsearch estar disponível

echo "🔍 Inicializando índices do Elasticsearch para OpenMetadata..."

# Aguardar Elasticsearch estar disponível
echo "⏳ Aguardando Elasticsearch estar disponível..."
until curl -s http://elasticsearch:9200/_cluster/health | grep -q '"status":"green\|yellow"'; do
    echo "   Aguardando Elasticsearch..."
    sleep 5
done

echo "✅ Elasticsearch disponível!"

# Função para criar índice
create_index() {
    local index_name=$1
    local mapping=$2
    
    echo "📊 Criando índice: $index_name"
    curl -X PUT "http://elasticsearch:9200/$index_name" \
         -H 'Content-Type: application/json' \
         -d "$mapping" \
         -s -o /dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Índice $index_name criado com sucesso"
    else
        echo "❌ Erro ao criar índice $index_name"
    fi
}

# Mapping básico para todos os índices
BASIC_MAPPING='{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "name": {"type": "text"},
      "displayName": {"type": "text"},
      "fullyQualifiedName": {"type": "keyword"},
      "description": {"type": "text"},
      "entityType": {"type": "keyword"},
      "service": {
        "properties": {
          "name": {"type": "keyword"},
          "type": {"type": "keyword"}
        }
      },
      "tags": {"type": "nested"},
      "owner": {"type": "nested"},
      "domain": {"type": "nested"}
    }
  }
}'

# Mapping específico para o índice "all"
ALL_INDEX_MAPPING='{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "name": {"type": "text"},
      "displayName": {"type": "text"},
      "fullyQualifiedName": {"type": "keyword"},
      "description": {"type": "text"},
      "entityType": {"type": "keyword"},
      "service": {
        "properties": {
          "name": {"type": "keyword"},
          "type": {"type": "keyword"}
        }
      },
      "tags": {"type": "nested"},
      "owner": {"type": "nested"},
      "domain": {"type": "nested"},
      "database": {"type": "nested"},
      "databaseSchema": {"type": "nested"}
    }
  }
}'

# Criar todos os índices necessários
echo "🚀 Criando índices do OpenMetadata..."

create_index "all" "$ALL_INDEX_MAPPING"
create_index "table_search_index" "$BASIC_MAPPING"
create_index "topic_search_index" "$BASIC_MAPPING"
create_index "dashboard_search_index" "$BASIC_MAPPING"
create_index "pipeline_search_index" "$BASIC_MAPPING"
create_index "mlmodel_search_index" "$BASIC_MAPPING"
create_index "container_search_index" "$BASIC_MAPPING"
create_index "search_entity_search_index" "$BASIC_MAPPING"
create_index "api_endpoint_search_index" "$BASIC_MAPPING"
create_index "database_search_index" "$BASIC_MAPPING"
create_index "databaseschema_search_index" "$BASIC_MAPPING"
create_index "test_case_search_index" "$BASIC_MAPPING"
create_index "test_suite_search_index" "$BASIC_MAPPING"
create_index "user_search_index" "$BASIC_MAPPING"
create_index "team_search_index" "$BASIC_MAPPING"
create_index "glossary_search_index" "$BASIC_MAPPING"
create_index "tag_search_index" "$BASIC_MAPPING"

echo "🎉 Inicialização dos índices concluída!"

# Verificar índices criados
echo "📋 Índices criados:"
curl -s "http://elasticsearch:9200/_cat/indices?v" | grep search_index
curl -s "http://elasticsearch:9200/_cat/indices?v" | grep -E "^[[:space:]]*[[:alnum:]]*[[:space:]]*all[[:space:]]"

echo "✅ Script de inicialização finalizado!"

