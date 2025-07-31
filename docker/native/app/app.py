"""
DataLake Native - Versão Baseada em Arquivos
Flask App com Jobs Agendados e Dashboard
Armazenamento: JSON files (S3-ready)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pandas as pd
import requests
import uuid
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração de storage
STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')  # local ou s3
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))  # Usar ./data por padrão

# Inicialização Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'datalake-native-dev'

# Funções de Storage
def ensure_data_structure():
    """Criar estrutura de pastas para dados"""
    folders = [
        DATA_DIR / 'raw' / 'weather',
        DATA_DIR / 'processed',
        DATA_DIR / 'logs',
        DATA_DIR / 'metrics'
    ]
    
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📁 Estrutura de dados criada em {DATA_DIR}")

def save_job_execution(execution_data):
    """Salvar execução de job em arquivo JSON"""
    today = datetime.now().strftime('%Y%m%d')
    file_path = DATA_DIR / 'logs' / f'jobs_{today}.json'
    
    # Carregar execuções existentes
    executions = []
    if file_path.exists():
        with open(file_path, 'r') as f:
            executions = json.load(f)
    
    # Adicionar nova execução
    executions.append(execution_data)
    
    # Salvar arquivo
    with open(file_path, 'w') as f:
        json.dump(executions, f, indent=2, default=str)

def save_weather_data(weather_data):
    """Salvar dados meteorológicos em arquivo JSON"""
    today = datetime.now().strftime('%Y%m%d')
    file_path = DATA_DIR / 'raw' / 'weather' / f'weather_{today}.json'
    
    # Carregar dados existentes
    data = []
    if file_path.exists():
        with open(file_path, 'r') as f:
            data = json.load(f)
    
    # Adicionar novos dados
    data.append(weather_data)
    
    # Salvar arquivo
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_job_executions(days=7):
    """Carregar execuções dos últimos N dias"""
    executions = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        file_path = DATA_DIR / 'logs' / f'jobs_{date}.json'
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                daily_executions = json.load(f)
                executions.extend(daily_executions)
    
    # Ordenar por timestamp (mais recente primeiro)
    executions.sort(key=lambda x: x['start_time'], reverse=True)
    return executions

def load_weather_data(hours=24):
    """Carregar dados meteorológicos das últimas N horas"""
    data = []
    
    # Verificar últimos 2 dias para cobrir 24h
    for i in range(2):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        file_path = DATA_DIR / 'raw' / 'weather' / f'weather_{date}.json'
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                daily_data = json.load(f)
                data.extend(daily_data)
    
    # Filtrar últimas N horas
    cutoff = datetime.now() - timedelta(hours=hours)
    filtered_data = []
    
    for record in data:
        record_time = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        if record_time >= cutoff:
            filtered_data.append(record)
    
    # Ordenar por timestamp
    filtered_data.sort(key=lambda x: x['timestamp'])
    return filtered_data

# Jobs
def collect_weather_data():
    """Job para coletar dados de temperatura de Campinas"""
    job_id = str(uuid.uuid4())
    job_name = "weather_collection"
    start_time = datetime.now()
    
    execution_data = {
        'id': job_id,
        'job_name': job_name,
        'status': 'running',
        'start_time': start_time.isoformat(),
        'end_time': None,
        'duration_seconds': None,
        'records_processed': 0,
        'error_message': None
    }
    
    try:
        logger.info(f"🌡️ Iniciando coleta de dados meteorológicos...")
        
        # Simular dados realísticos para Campinas
        import random
        
        temperature = round(random.uniform(18, 32), 1)  # Temperatura típica de Campinas
        humidity = round(random.uniform(40, 85), 1)
        pressure = round(random.uniform(1010, 1025), 1)
        
        # Condições climáticas aleatórias
        conditions = ['Ensolarado', 'Nublado', 'Parcialmente nublado', 'Chuvoso', 'Garoa']
        description = random.choice(conditions)
        
        weather_data = {
            'id': str(uuid.uuid4()),
            'city': 'Campinas',
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'job_execution_id': job_id
        }
        
        # Salvar dados meteorológicos
        save_weather_data(weather_data)
        
        # Finalizar job com sucesso
        end_time = datetime.now()
        execution_data.update({
            'status': 'success',
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'records_processed': 1
        })
        
        # Salvar execução
        save_job_execution(execution_data)
        
        logger.info(f"✅ Dados coletados: {temperature}°C, {humidity}% umidade, {description}")
        
    except Exception as e:
        # Registrar erro
        end_time = datetime.now()
        execution_data.update({
            'status': 'error',
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'error_message': str(e)
        })
        
        # Salvar execução com erro
        save_job_execution(execution_data)
        
        logger.error(f"❌ Erro na coleta: {e}")

# Scheduler
scheduler = BackgroundScheduler()

# Routes
@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """API para métricas do dashboard"""
    try:
        # Carregar execuções
        executions = load_job_executions(days=30)
        
        # Calcular métricas
        total_jobs = len(executions)
        successful_jobs = len([e for e in executions if e['status'] == 'success'])
        failed_jobs = len([e for e in executions if e['status'] == 'error'])
        
        # Jobs hoje
        today = datetime.now().date()
        jobs_today = len([
            e for e in executions 
            if datetime.fromisoformat(e['start_time']).date() == today
        ])
        
        # Última execução
        last_execution = executions[0] if executions else None
        
        # Taxa de sucesso
        success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        return jsonify({
            'total_jobs': total_jobs,
            'successful_jobs': successful_jobs,
            'failed_jobs': failed_jobs,
            'jobs_today': jobs_today,
            'success_rate': round(success_rate, 1),
            'last_execution': last_execution
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather')
def get_weather_data():
    """API para dados de temperatura"""
    try:
        hours = request.args.get('hours', 24, type=int)
        data = load_weather_data(hours=hours)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados meteorológicos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs')
def get_job_executions():
    """API para histórico de execuções"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Carregar todas as execuções
        all_executions = load_job_executions(days=30)
        
        # Paginação manual
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        executions = all_executions[start_idx:end_idx]
        
        total = len(all_executions)
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'executions': executions,
            'total': total,
            'pages': pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar execuções: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/trigger/<job_name>', methods=['POST'])
def trigger_job(job_name):
    """Trigger manual de job"""
    try:
        if job_name == 'weather_collection':
            collect_weather_data()
            return jsonify({'message': f'Job {job_name} executado com sucesso'})
        else:
            return jsonify({'error': 'Job não encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Erro ao executar job {job_name}: {e}")
        return jsonify({'error': str(e)}), 500

# Inicialização
def init_app():
    """Inicializar aplicação"""
    # Criar estrutura de dados
    ensure_data_structure()
    
    # Configurar scheduler
    scheduler.add_job(
        func=collect_weather_data,
        trigger=IntervalTrigger(minutes=30),  # A cada 30 minutos
        id='weather_collection',
        name='Coleta de Dados Meteorológicos',
        replace_existing=True
    )
    
    # Executar uma coleta inicial se não houver dados
    weather_data = load_weather_data(hours=1)
    if not weather_data:
        logger.info("🔄 Executando coleta inicial...")
        collect_weather_data()
    
    # Iniciar scheduler
    if not scheduler.running:
        scheduler.start()
    
    logger.info("🚀 DataLake Native iniciado com sucesso!")
    logger.info("📊 Dashboard: http://localhost:5420")
    logger.info("🔄 Job agendado: coleta a cada 30 minutos")
    logger.info(f"📁 Dados salvos em: {DATA_DIR}")

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

