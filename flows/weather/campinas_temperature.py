"""
Simple Campinas Temperature Data Collection Pipeline
Collects temperature data from Campinas and stores in local files
"""

import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
from typing import Dict, Any


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=10))
def get_campinas_temperature() -> Dict[str, Any]:
    """Get current temperature data for Campinas, SP, Brazil"""
    print("🌡️ Fetching temperature data for Campinas...")
    
    try:
        # Using wttr.in (free weather service)
        url = "https://wttr.in/Campinas,Brazil?format=j1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract current weather data
        current = data['current_condition'][0]
        location = data['nearest_area'][0]
        
        temperature_data = {
            'timestamp': datetime.now().isoformat(),
            'city': 'Campinas',
            'state': 'São Paulo',
            'country': 'Brazil',
            'temperature_celsius': float(current['temp_C']),
            'temperature_fahrenheit': float(current['temp_F']),
            'feels_like_celsius': float(current['FeelsLikeC']),
            'humidity': int(current['humidity']),
            'weather_description': current['weatherDesc'][0]['value'],
            'wind_speed_kmh': float(current['windspeedKmph']),
            'wind_direction': current['winddir16Point'],
            'pressure_mb': float(current['pressure']),
            'visibility_km': float(current['visibility']),
            'uv_index': float(current['uvIndex']),
            'cloud_cover': int(current['cloudcover']),
            'latitude': float(location['latitude']),
            'longitude': float(location['longitude'])
        }
        
        print(f"✅ Temperature data collected:")
        print(f"   🌡️ Temperature: {temperature_data['temperature_celsius']}°C")
        print(f"   💧 Humidity: {temperature_data['humidity']}%")
        print(f"   🌤️ Weather: {temperature_data['weather_description']}")
        
        return temperature_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching weather data: {e}")
        # Return mock data for demo purposes
        return {
            'timestamp': datetime.now().isoformat(),
            'city': 'Campinas',
            'state': 'São Paulo',
            'country': 'Brazil',
            'temperature_celsius': 22.5,
            'temperature_fahrenheit': 72.5,
            'feels_like_celsius': 24.0,
            'humidity': 65,
            'weather_description': 'Partly cloudy',
            'wind_speed_kmh': 10.0,
            'wind_direction': 'SE',
            'pressure_mb': 1013.0,
            'visibility_km': 10.0,
            'uv_index': 5.0,
            'cloud_cover': 30,
            'latitude': -22.9056,
            'longitude': -47.0608,
            'note': 'Mock data - API unavailable'
        }
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise


@task
def validate_temperature_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean temperature data"""
    print("🔍 Validating temperature data...")
    
    # Basic validation
    required_fields = [
        'timestamp', 'city', 'temperature_celsius', 
        'humidity', 'weather_description'
    ]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Data quality checks
    temp_c = data['temperature_celsius']
    humidity = data['humidity']
    
    # Reasonable temperature range for Campinas (-10°C to 50°C)
    if not -10 <= temp_c <= 50:
        print(f"⚠️ Warning: Temperature {temp_c}°C seems unusual for Campinas")
    
    # Humidity should be 0-100%
    if not 0 <= humidity <= 100:
        print(f"⚠️ Warning: Humidity {humidity}% is outside valid range")
        data['humidity'] = max(0, min(100, humidity))  # Clamp to valid range
    
    # Add data quality score
    quality_score = 100
    if 'note' in data and 'Mock data' in data['note']:
        quality_score = 50  # Lower score for mock data
    
    data['data_quality_score'] = quality_score
    data['validation_timestamp'] = datetime.now().isoformat()
    
    print(f"✅ Data validation completed (Quality Score: {quality_score}%)")
    return data


@task
def save_temperature_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Save temperature data to local S3 simulation structure"""
    print("💾 Saving temperature data to local S3 structure...")
    
    try:
        # Use S3 simulation structure
        staging_dir = "/app/s3/staging/weather"
        raw_dir = "/app/s3/raw/weather"
        
        # Ensure directories exist (they should from Docker copy)
        os.makedirs(staging_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)
        
        # File paths
        staging_json = f"{staging_dir}/campinas_temperature_latest.json"
        raw_csv = f"{raw_dir}/campinas_temperature_history.csv"
        
        # Save latest reading to staging
        print(f"📄 Saving to staging: {staging_json}")
        with open(staging_json, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Append to raw CSV history
        print(f"📊 Updating raw history: {raw_csv}")
        
        if os.path.exists(raw_csv):
            # Read existing CSV
            df_existing = pd.read_csv(raw_csv)
            print(f"   Found existing CSV with {len(df_existing)} records")
        else:
            # Create new DataFrame
            df_existing = pd.DataFrame()
            print("   Creating new CSV file")
        
        # Add new data
        df_new = pd.DataFrame([data])
        
        if not df_existing.empty:
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            # Remove duplicates based on timestamp
            df_combined = df_combined.drop_duplicates(subset=['timestamp'], keep='last')
            df_combined = df_combined.sort_values('timestamp')
        else:
            df_combined = df_new
        
        # Save updated CSV
        df_combined.to_csv(raw_csv, index=False)
        
        print(f"✅ Temperature data saved:")
        print(f"   📄 Staging: {staging_json}")
        print(f"   📊 Raw: {raw_csv} ({len(df_combined)} records)")
        
        return {
            'staging_json': staging_json,
            'raw_csv': raw_csv,
            'total_records': len(df_combined)
        }
        
    except Exception as e:
        print(f"❌ Error saving temperature data: {e}")
        raise


@task
def generate_temperature_summary(file_info: Dict[str, str]) -> Dict[str, Any]:
    """Generate summary statistics from temperature data"""
    print("📈 Generating temperature summary...")
    
    try:
        csv_path = file_info['raw_csv']
        
        if not os.path.exists(csv_path):
            return {"error": "No temperature data found"}
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return {"error": "No temperature data found in CSV"}
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate summary statistics
        summary = {
            'total_records': len(df),
            'data_source': csv_path,
            'date_range': {
                'first_record': df['timestamp'].min().isoformat(),
                'last_record': df['timestamp'].max().isoformat(),
                'days_covered': (df['timestamp'].max() - df['timestamp'].min()).days + 1
            },
            'temperature_stats': {
                'current_celsius': float(df.iloc[-1]['temperature_celsius']),
                'avg_celsius': round(df['temperature_celsius'].mean(), 2),
                'min_celsius': float(df['temperature_celsius'].min()),
                'max_celsius': float(df['temperature_celsius'].max()),
                'std_celsius': round(df['temperature_celsius'].std(), 2)
            },
            'humidity_stats': {
                'current_percent': int(df.iloc[-1]['humidity']),
                'avg_percent': round(df['humidity'].mean(), 1),
                'min_percent': int(df['humidity'].min()),
                'max_percent': int(df['humidity'].max())
            },
            'data_quality': {
                'avg_quality_score': round(df['data_quality_score'].mean(), 1),
                'mock_data_percentage': round((df['data_quality_score'] < 100).mean() * 100, 1)
            },
            's3_structure': {
                'staging_layer': '/app/s3/staging/weather/',
                'raw_layer': '/app/s3/raw/weather/',
                'trusted_layer': '/app/s3/trusted/weather/',
                'refined_layer': '/app/s3/refined/weather/'
            }
        }
        
        print(f"📊 Temperature Summary:")
        print(f"   📈 Records: {summary['total_records']}")
        print(f"   🌡️ Current: {summary['temperature_stats']['current_celsius']}°C")
        print(f"   📊 Average: {summary['temperature_stats']['avg_celsius']}°C")
        print(f"   📉 Range: {summary['temperature_stats']['min_celsius']}°C - {summary['temperature_stats']['max_celsius']}°C")
        print(f"   🗂️ S3 Structure: staging → raw → trusted → refined")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return {"error": str(e)}


@flow(
    name="Campinas Temperature Monitor",
    description="Collects and stores temperature data for Campinas, SP",
    log_prints=True
)
def campinas_temperature_pipeline():
    """
    Main temperature monitoring pipeline:
    1. Fetch current temperature data for Campinas
    2. Validate and clean the data
    3. Save to local files (JSON + CSV)
    4. Generate summary statistics
    """
    print("🚀 Starting Campinas Temperature Pipeline...")
    
    # Fetch temperature data
    temperature_data = get_campinas_temperature()
    
    # Validate data
    validated_data = validate_temperature_data(temperature_data)
    
    # Save to files
    file_info = save_temperature_data(validated_data)
    
    # Generate summary
    summary = generate_temperature_summary(file_info)
    
    print("🎉 Campinas Temperature Pipeline completed!")
    
    return {
        'pipeline_status': 'completed',
        'temperature_celsius': validated_data['temperature_celsius'],
        'weather_description': validated_data['weather_description'],
        'files_saved': file_info,
        'summary': summary,
        'execution_time': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running Campinas Temperature Pipeline locally...")
    
    result = campinas_temperature_pipeline()
    print(f"🎯 Pipeline result: {result['pipeline_status']}")
    print(f"🌡️ Current temperature: {result['temperature_celsius']}°C")
    print(f"🌤️ Weather: {result['weather_description']}")
    print(f"💾 Files saved: {result['files_saved']['total_records']} records")

