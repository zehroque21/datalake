"""
Campinas Temperature Pipeline with Local Staging (Simulating S3 Structure)
Collects temperature data from Campinas and stores in local file system
with S3-like directory structure for staging purposes
"""

import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
from typing import Dict, Any
from pathlib import Path


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
def create_staging_directories() -> str:
    """Create staging directory structure simulating S3 bucket organization"""
    print("📁 Creating staging directory structure...")
    
    # Base staging directory (simulating S3 bucket)
    staging_base = "/app/data/staging"
    
    # Create directory structure similar to S3
    directories = [
        f"{staging_base}/weather/campinas/latest",
        f"{staging_base}/weather/campinas/hourly",
        f"{staging_base}/weather/campinas/daily",
        f"{staging_base}/weather/campinas/monthly",
        f"{staging_base}/weather/campinas/raw"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Staging directories created at: {staging_base}")
    return staging_base


@task
def load_to_staging(data: Dict[str, Any], staging_base: str) -> Dict[str, str]:
    """Load temperature data to local staging area with S3-like structure"""
    print("💾 Loading temperature data to staging area...")
    
    try:
        # Generate file paths with S3-like structure
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y/%m/%d')
        hour_str = timestamp.strftime('%H')
        month_str = timestamp.strftime('%Y/%m')
        
        # Paths for different file types (simulating S3 structure)
        paths = {
            'latest_json': f'{staging_base}/weather/campinas/latest/temperature.json',
            'hourly_json': f'{staging_base}/weather/campinas/hourly/{date_str}/temperature_{hour_str}.json',
            'daily_csv': f'{staging_base}/weather/campinas/daily/{date_str}/temperature_history.csv',
            'monthly_summary': f'{staging_base}/weather/campinas/monthly/{month_str}/summary.json',
            'raw_json': f'{staging_base}/weather/campinas/raw/{timestamp.strftime("%Y%m%d_%H%M%S")}.json'
        }
        
        # Create subdirectories as needed
        for path in paths.values():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Save latest reading as JSON
        print(f"📄 Saving latest reading: {paths['latest_json']}")
        with open(paths['latest_json'], 'w') as f:
            json.dump(data, f, indent=2)
        
        # 2. Save hourly reading as JSON
        print(f"📄 Saving hourly reading: {paths['hourly_json']}")
        with open(paths['hourly_json'], 'w') as f:
            json.dump(data, f, indent=2)
        
        # 3. Save raw data with timestamp
        print(f"📄 Saving raw data: {paths['raw_json']}")
        with open(paths['raw_json'], 'w') as f:
            json.dump(data, f, indent=2)
        
        # 4. Append to daily CSV (read existing, append, write back)
        print(f"📊 Updating daily CSV: {paths['daily_csv']}")
        
        if os.path.exists(paths['daily_csv']):
            # Read existing CSV
            df_existing = pd.read_csv(paths['daily_csv'])
            print(f"   Found existing CSV with {len(df_existing)} records")
        else:
            # Create new DataFrame
            df_existing = pd.DataFrame()
            print("   Creating new daily CSV file")
        
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
        df_combined.to_csv(paths['daily_csv'], index=False)
        
        # 5. Update monthly summary
        print(f"📈 Updating monthly summary: {paths['monthly_summary']}")
        monthly_summary = {
            'month': month_str,
            'total_records': len(df_combined),
            'avg_temperature': round(df_combined['temperature_celsius'].mean(), 2),
            'min_temperature': float(df_combined['temperature_celsius'].min()),
            'max_temperature': float(df_combined['temperature_celsius'].max()),
            'avg_humidity': round(df_combined['humidity'].mean(), 1),
            'last_updated': datetime.now().isoformat(),
            'data_quality_avg': round(df_combined['data_quality_score'].mean(), 1)
        }
        
        with open(paths['monthly_summary'], 'w') as f:
            json.dump(monthly_summary, f, indent=2)
        
        print(f"✅ Temperature data saved to staging:")
        print(f"   📄 Latest: {paths['latest_json']}")
        print(f"   📄 Hourly: {paths['hourly_json']}")
        print(f"   📊 Daily CSV: {paths['daily_csv']} ({len(df_combined)} records)")
        print(f"   📈 Monthly: {paths['monthly_summary']}")
        print(f"   📄 Raw: {paths['raw_json']}")
        
        return {
            'staging_base': staging_base,
            'latest_json': paths['latest_json'],
            'hourly_json': paths['hourly_json'],
            'daily_csv': paths['daily_csv'],
            'monthly_summary': paths['monthly_summary'],
            'raw_json': paths['raw_json'],
            'total_records': len(df_combined)
        }
        
    except Exception as e:
        print(f"❌ Error saving to staging: {e}")
        raise


@task
def generate_staging_summary(staging_info: Dict[str, str]) -> Dict[str, Any]:
    """Generate summary from staging area data"""
    print("📈 Generating temperature summary from staging area...")
    
    try:
        csv_path = staging_info['daily_csv']
        
        if not os.path.exists(csv_path):
            return {"error": "No temperature data found in staging"}
        
        # Read CSV from staging
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return {"error": "No temperature data found in CSV"}
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate summary statistics
        summary = {
            'total_records': len(df),
            'data_source': f"staging://{csv_path}",
            'staging_structure': {
                'base_path': staging_info['staging_base'],
                'latest_file': staging_info['latest_json'],
                'daily_csv': staging_info['daily_csv'],
                'monthly_summary': staging_info['monthly_summary']
            },
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
            }
        }
        
        print(f"📊 Temperature Summary (from staging):")
        print(f"   📈 Records: {summary['total_records']}")
        print(f"   🌡️ Current: {summary['temperature_stats']['current_celsius']}°C")
        print(f"   📊 Average: {summary['temperature_stats']['avg_celsius']}°C")
        print(f"   📉 Range: {summary['temperature_stats']['min_celsius']}°C - {summary['temperature_stats']['max_celsius']}°C")
        print(f"   💾 Staging: {staging_info['staging_base']}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error generating staging summary: {e}")
        return {"error": str(e)}


@flow(
    name="Campinas Temperature Monitor (Staging)",
    description="Collects and stores temperature data for Campinas, SP in local staging area with S3-like structure",
    log_prints=True
)
def campinas_temperature_staging_pipeline():
    """
    Main temperature monitoring pipeline with local staging:
    1. Fetch current temperature data for Campinas
    2. Validate and clean the data
    3. Create staging directory structure (simulating S3)
    4. Store in multiple formats and locations
    5. Generate summary statistics from staging data
    """
    print("🚀 Starting Campinas Temperature Pipeline (Local Staging)...")
    
    # Fetch temperature data
    temperature_data = get_campinas_temperature()
    
    # Validate data
    validated_data = validate_temperature_data(temperature_data)
    
    # Create staging directories
    staging_base = create_staging_directories()
    
    # Load to staging area
    staging_info = load_to_staging(validated_data, staging_base)
    
    # Generate summary from staging
    summary = generate_staging_summary(staging_info)
    
    print("🎉 Campinas Temperature Pipeline (Local Staging) completed!")
    
    return {
        'pipeline_status': 'completed',
        'temperature_celsius': validated_data['temperature_celsius'],
        'weather_description': validated_data['weather_description'],
        'storage_type': 'local_staging',
        'staging_info': staging_info,
        'summary': summary,
        'execution_time': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running Campinas Temperature Pipeline (Local Staging) locally...")
    
    result = campinas_temperature_staging_pipeline()
    print(f"🎯 Pipeline result: {result['pipeline_status']}")
    print(f"🌡️ Current temperature: {result['temperature_celsius']}°C")
    print(f"🌤️ Weather: {result['weather_description']}")
    print(f"💾 Stored in staging: {result['staging_info']['staging_base']}")

