"""
DataLake Native - File-Based Version
Flask App com Jobs Agendados e Storage em Arquivos
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pandas as pd
import random

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'datalake-native-dev'

# Configuração de storage
STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')  # local ou s3
DATA_DIR = Path('/app/data')  # No container
if not DATA_DIR.exists():
    DATA_DIR = Path('./data')  # Para desenvolvimento local

# Criar estrutura de pastas
for folder in ['raw/weather', 'processed', 'logs', 'metrics']:
    (DATA_DIR / folder).mkdir(parents=True, exist_ok=True)

# Scheduler
scheduler = BackgroundScheduler()

class DataLakeStorage:
    """Classe para gerenciar storage de dados"""
    
    @staticmethod
    def save_job_execution(job_data):
        """Salvar execução de job"""
        today = datetime.now().strftime('%Y%m%d')
        file_path = DATA_DIR / 'logs' / f'jobs_{today}.json'
        
        # Carregar execuções existentes
        executions = []
        if file_path.exists():
            with open(file_path, 'r') as f:
                executions = json.load(f)
        
        # Adicionar nova execução
        executions.append(job_data)
        
        # Salvar
        with open(file_path, 'w') as f:
            json.dump(executions, f, indent=2, default=str)
    
    @staticmethod
    def save_weather_data(weather_data):
        """Salvar dados meteorológicos"""
        today = datetime.now().strftime('%Y%m%d')
        file_path = DATA_DIR / 'raw' / 'weather' / f'weather_{today}.json'
        
        # Carregar dados existentes
        data = []
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        
        # Adicionar novos dados
        data.append(weather_data)
        
        # Salvar
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def get_job_executions(days=7):
        """Obter execuções de jobs dos últimos N dias"""
        executions = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')
            file_path = DATA_DIR / 'logs' / f'jobs_{date_str}.json'
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    daily_executions = json.load(f)
                    executions.extend(daily_executions)
        
        # Ordenar por timestamp (mais recente primeiro)
        executions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        return executions
    
    @staticmethod
    def get_weather_data(days=2):
        """Obter dados meteorológicos dos últimos N dias"""
        weather_data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')
            file_path = DATA_DIR / 'raw' / 'weather' / f'weather_{date_str}.json'
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    daily_data = json.load(f)
                    weather_data.extend(daily_data)
        
        # Ordenar por timestamp (mais recente primeiro)
        weather_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return weather_data
    
    @staticmethod
    def calculate_metrics():
        """Calcular métricas em tempo real"""
        executions = DataLakeStorage.get_job_executions(days=1)  # Apenas hoje
        
        today = datetime.now().date()
        jobs_today = len([e for e in executions if datetime.fromisoformat(e['start_time']).date() == today])
        successful_jobs = len([e for e in executions if e['status'] == 'success' and datetime.fromisoformat(e['start_time']).date() == today])
        failed_jobs = len([e for e in executions if e['status'] == 'error' and datetime.fromisoformat(e['start_time']).date() == today])
        
        total_executions = DataLakeStorage.get_job_executions(days=30)  # Último mês
        total_jobs = len(total_executions)
        
        success_rate = (successful_jobs / jobs_today * 100) if jobs_today > 0 else 0
        
        last_execution = executions[0] if executions else None
        
        return {
            'jobs_today': jobs_today,
            'successful_jobs': successful_jobs,
            'failed_jobs': failed_jobs,
            'total_jobs': total_jobs,
            'success_rate': round(success_rate, 1),
            'last_execution': last_execution
        }

def collect_weather_data():
    """Job para coletar dados de temperatura de Campinas"""
    job_name = "weather_collection"
    start_time = datetime.now()
    
    job_data = {
        'id': f"{job_name}_{start_time.strftime('%Y%m%d_%H%M%S')}",
        'job_name': job_name,
        'status': 'running',
        'start_time': start_time.isoformat(),
        'end_time': None,
        'duration_seconds': None,
        'records_processed': 0,
        'error_message': None
    }
    
    try:
        # Simular coleta de dados (substitua por API real)
        temperature = round(random.uniform(18, 32), 1)  # Temperatura típica de Campinas
        humidity = round(random.uniform(45, 85), 1)      # Umidade típica
        pressure = round(random.uniform(1010, 1025), 1)  # Pressão atmosférica
        
        descriptions = [
            "Ensolarado", "Parcialmente nublado", "Nublado", 
            "Chuva leve", "Tempo limpo", "Neblina"
        ]
        description = random.choice(descriptions)
        
        # Dados meteorológicos
        weather_data = {
            'id': f"weather_{start_time.strftime('%Y%m%d_%H%M%S')}",
            'city': "Campinas",
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'description': description,
            'timestamp': start_time.isoformat(),
            'job_execution_id': job_data['id']
        }
        
        # Salvar dados meteorológicos
        DataLakeStorage.save_weather_data(weather_data)
        
        # Finalizar job com sucesso
        end_time = datetime.now()
        job_data.update({
            'status': 'success',
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'records_processed': 1
        })
        
        logger.info(f"✅ Dados coletados: {temperature}°C, {humidity}% umidade")
        
    except Exception as e:
        # Registrar erro
        end_time = datetime.now()
        job_data.update({
            'status': 'error',
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'error_message': str(e)
        })
        
        logger.error(f"❌ Erro na coleta: {e}")
    
    # Salvar execução do job
    DataLakeStorage.save_job_execution(job_data)

# Routes
@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """API para métricas gerais"""
    try:
        metrics = DataLakeStorage.calculate_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Erro ao calcular métricas: {e}")
        return jsonify({
            'jobs_today': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'total_jobs': 0,
            'success_rate': 0,
            'last_execution': None
        })

@app.route('/api/weather')
def get_weather_data():
    """API para dados meteorológicos"""
    try:
        weather_data = DataLakeStorage.get_weather_data(days=2)
        return jsonify(weather_data[:48])  # Últimas 48 horas
    except Exception as e:
        logger.error(f"Erro ao buscar dados meteorológicos: {e}")
        return jsonify([])

@app.route('/api/jobs')
def get_jobs():
    """API para execuções de jobs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        executions = DataLakeStorage.get_job_executions(days=7)
        
        # Paginação manual
        start = (page - 1) * per_page
        end = start + per_page
        paginated_executions = executions[start:end]
        
        total = len(executions)
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'executions': paginated_executions,
            'total': total,
            'pages': pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar execuções: {e}")
        return jsonify({
            'executions': [],
            'total': 0,
            'pages': 0,
            'current_page': 1
        })

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

@app.route('/api/storage/info')
def storage_info():
    """Informações sobre o storage"""
    try:
        info = {
            'storage_type': STORAGE_TYPE,
            'data_dir': str(DATA_DIR),
            'folders': {
                'raw': len(list((DATA_DIR / 'raw').rglob('*.json'))),
                'processed': len(list((DATA_DIR / 'processed').rglob('*.json'))),
                'logs': len(list((DATA_DIR / 'logs').rglob('*.json'))),
                'metrics': len(list((DATA_DIR / 'metrics').rglob('*.json')))
            },
            'total_files': len(list(DATA_DIR.rglob('*.json')))
        }
        return jsonify(info)
    except Exception as e:
        logger.error(f"Erro ao obter info do storage: {e}")
        return jsonify({'error': str(e)}), 500

# Inicialização automática
try:
    # Iniciar scheduler se não estiver rodando
    if not scheduler.running:
        scheduler.start()
        
    # Adicionar job se não existir
    if not scheduler.get_job('weather_collection'):
        scheduler.add_job(
            func=collect_weather_data,
            trigger=IntervalTrigger(minutes=30),
            id='weather_collection',
            name='Coleta de Dados Meteorológicos',
            replace_existing=True
        )
        
    # Executar coleta inicial se não houver dados hoje
    today = datetime.now().strftime('%Y%m%d')
    weather_file = DATA_DIR / 'raw' / 'weather' / f'weather_{today}.json'
    if not weather_file.exists():
        collect_weather_data()
        logger.info("🌡️ Coleta inicial de dados executada")
        
    logger.info("🚀 DataLake Native (File-Based) iniciado com sucesso!")
    logger.info(f"📁 Storage: {STORAGE_TYPE} - {DATA_DIR}")
    logger.info("🔄 Job agendado: coleta a cada 30 minutos")
    
except Exception as e:
    logger.error(f"❌ Erro na inicialização: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

