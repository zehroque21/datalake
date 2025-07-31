#!/usr/bin/env python3
"""
DataLake Native - Versão Simples
Flask App com Jobs Agendados e Dashboard
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pandas as pd
import requests
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'datalake-native-dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datalake.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database
db = SQLAlchemy(app)

# Criar tabelas automaticamente quando o app inicializar
@app.before_first_request
def create_tables():
    """Criar tabelas automaticamente na primeira requisição"""
    try:
        db.create_all()
        logger.info("✅ Tabelas do banco criadas com sucesso")
        
        # Executar coleta inicial se não houver dados
        if WeatherData.query.count() == 0:
            collect_weather_data()
            logger.info("🌡️ Coleta inicial de dados executada")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")

# Models
class JobExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, error, running
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Float)
    records_processed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    pressure = db.Column(db.Float)
    description = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    job_execution_id = db.Column(db.Integer, db.ForeignKey('job_execution.id'))

# Jobs
def collect_weather_data():
    """Job para coletar dados de temperatura de Campinas"""
    job_name = "weather_collection"
    start_time = datetime.utcnow()
    
    # Registrar início do job
    execution = JobExecution(
        job_name=job_name,
        status='running',
        start_time=start_time
    )
    db.session.add(execution)
    db.session.commit()
    
    try:
        logger.info(f"🌡️ Iniciando coleta de dados meteorológicos...")
        
        # API OpenWeatherMap (simulação - você pode usar sua API key)
        # Por enquanto, vamos simular dados
        import random
        
        # Simular dados realísticos para Campinas
        temperature = round(random.uniform(18, 32), 1)  # Temperatura típica de Campinas
        humidity = round(random.uniform(40, 85), 1)
        pressure = round(random.uniform(1010, 1025), 1)
        
        weather_data = WeatherData(
            city='Campinas',
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            description='Dados simulados',
            job_execution_id=execution.id
        )
        
        db.session.add(weather_data)
        
        # Finalizar job com sucesso
        end_time = datetime.utcnow()
        execution.status = 'success'
        execution.end_time = end_time
        execution.duration_seconds = (end_time - start_time).total_seconds()
        execution.records_processed = 1
        
        db.session.commit()
        
        logger.info(f"✅ Dados coletados: {temperature}°C, {humidity}% umidade")
        
    except Exception as e:
        # Registrar erro
        end_time = datetime.utcnow()
        execution.status = 'error'
        execution.end_time = end_time
        execution.duration_seconds = (end_time - start_time).total_seconds()
        execution.error_message = str(e)
        
        db.session.commit()
        
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
        # Métricas básicas
        total_jobs = JobExecution.query.count()
        successful_jobs = JobExecution.query.filter_by(status='success').count()
        failed_jobs = JobExecution.query.filter_by(status='error').count()
        
        # Jobs hoje
        today = datetime.utcnow().date()
        jobs_today = JobExecution.query.filter(
            db.func.date(JobExecution.created_at) == today
        ).count()
        
        # Última execução
        last_execution = JobExecution.query.order_by(
            JobExecution.created_at.desc()
        ).first()
        
        # Taxa de sucesso
        success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        return jsonify({
            'total_jobs': total_jobs,
            'successful_jobs': successful_jobs,
            'failed_jobs': failed_jobs,
            'jobs_today': jobs_today,
            'success_rate': round(success_rate, 1),
            'last_execution': {
                'job_name': last_execution.job_name if last_execution else None,
                'status': last_execution.status if last_execution else None,
                'timestamp': last_execution.created_at.isoformat() if last_execution else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather')
def get_weather_data():
    """API para dados de temperatura"""
    try:
        # Últimas 24 horas de dados
        since = datetime.utcnow() - timedelta(hours=24)
        
        weather_records = WeatherData.query.filter(
            WeatherData.timestamp >= since
        ).order_by(WeatherData.timestamp.desc()).limit(48).all()
        
        data = []
        for record in reversed(weather_records):  # Ordem cronológica
            data.append({
                'timestamp': record.timestamp.isoformat(),
                'temperature': record.temperature,
                'humidity': record.humidity,
                'pressure': record.pressure
            })
        
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
        
        executions = JobExecution.query.order_by(
            JobExecution.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = []
        for execution in executions.items:
            data.append({
                'id': execution.id,
                'job_name': execution.job_name,
                'status': execution.status,
                'start_time': execution.start_time.isoformat(),
                'end_time': execution.end_time.isoformat() if execution.end_time else None,
                'duration_seconds': execution.duration_seconds,
                'records_processed': execution.records_processed,
                'error_message': execution.error_message
            })
        
        return jsonify({
            'executions': data,
            'total': executions.total,
            'pages': executions.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar execuções: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/trigger/<job_name>')
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
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Configurar scheduler
        scheduler.add_job(
            func=collect_weather_data,
            trigger=IntervalTrigger(minutes=30),  # A cada 30 minutos
            id='weather_collection',
            name='Coleta de Dados Meteorológicos',
            replace_existing=True
        )
        
        # Executar uma coleta inicial
        collect_weather_data()
        
        # Iniciar scheduler
        if not scheduler.running:
            scheduler.start()
        
        logger.info("🚀 DataLake Native iniciado com sucesso!")
        logger.info("📊 Dashboard: http://localhost:5000")
        logger.info("🔄 Job agendado: coleta a cada 30 minutos")

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

