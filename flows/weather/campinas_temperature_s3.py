"""
Campinas Temperature Pipeline with S3 Storage
Collects temperature data from Campinas and stores in AWS S3 bucket
"""

import pandas as pd
import requests
import boto3
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
import os
from typing import Dict, Any
from io import StringIO


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
def get_s3_client():
    """Get S3 client with credentials from environment or AWS profile"""
    print("🔐 Initializing S3 client...")
    
    try:
        # Try to use environment variables first
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            print("   Using AWS credentials from environment variables")
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        else:
            # Fall back to AWS profile or IAM role
            print("   Using AWS credentials from profile/IAM role")
            s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        
        # Test connection
        s3_client.list_buckets()
        print("✅ S3 client initialized successfully")
        return s3_client
        
    except Exception as e:
        print(f"❌ Error initializing S3 client: {e}")
        print("💡 Make sure AWS credentials are configured:")
        print("   - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables, OR")
        print("   - Configure AWS CLI with 'aws configure', OR")
        print("   - Use IAM roles if running on EC2")
        raise


@task
def load_to_s3_bucket(data: Dict[str, Any], s3_client) -> Dict[str, str]:
    """Load temperature data to S3 bucket"""
    print("☁️ Loading temperature data to S3...")
    
    try:
        # Configuration
        bucket_name = os.getenv('S3_BUCKET_NAME', 'datalake-amadoroque-bucket')
        
        # Generate file paths
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y/%m/%d')
        hour_str = timestamp.strftime('%H')
        
        # Paths for different file types
        paths = {
            'latest_json': 'weather/campinas/latest/temperature.json',
            'hourly_json': f'weather/campinas/hourly/{date_str}/temperature_{hour_str}.json',
            'daily_csv': f'weather/campinas/daily/{date_str}/temperature_history.csv'
        }
        
        # 1. Save latest reading as JSON
        print(f"📄 Saving latest reading to: s3://{bucket_name}/{paths['latest_json']}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=paths['latest_json'],
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            Metadata={
                'source': 'campinas-temperature-pipeline',
                'timestamp': data['timestamp'],
                'temperature': str(data['temperature_celsius']),
                'weather': data['weather_description']
            }
        )
        
        # 2. Save hourly reading as JSON
        print(f"📄 Saving hourly reading to: s3://{bucket_name}/{paths['hourly_json']}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=paths['hourly_json'],
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
        
        # 3. Append to daily CSV (read existing, append, write back)
        print(f"📊 Updating daily CSV: s3://{bucket_name}/{paths['daily_csv']}")
        
        try:
            # Try to read existing CSV
            response = s3_client.get_object(Bucket=bucket_name, Key=paths['daily_csv'])
            existing_csv = response['Body'].read().decode('utf-8')
            df_existing = pd.read_csv(StringIO(existing_csv))
            print(f"   Found existing CSV with {len(df_existing)} records")
        except s3_client.exceptions.NoSuchKey:
            # File doesn't exist, create new DataFrame
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
        csv_buffer = StringIO()
        df_combined.to_csv(csv_buffer, index=False)
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=paths['daily_csv'],
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        print(f"✅ Temperature data saved to S3:")
        print(f"   📄 Latest JSON: s3://{bucket_name}/{paths['latest_json']}")
        print(f"   📄 Hourly JSON: s3://{bucket_name}/{paths['hourly_json']}")
        print(f"   📊 Daily CSV: s3://{bucket_name}/{paths['daily_csv']} ({len(df_combined)} records)")
        
        return {
            'bucket': bucket_name,
            'latest_json': paths['latest_json'],
            'hourly_json': paths['hourly_json'],
            'daily_csv': paths['daily_csv'],
            'total_records': len(df_combined)
        }
        
    except Exception as e:
        print(f"❌ Error saving to S3: {e}")
        raise


@task
def generate_s3_summary(s3_client, bucket_info: Dict[str, str]) -> Dict[str, Any]:
    """Generate summary from S3 stored data"""
    print("📈 Generating temperature summary from S3...")
    
    try:
        bucket_name = bucket_info['bucket']
        csv_key = bucket_info['daily_csv']
        
        # Read CSV from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=csv_key)
        csv_content = response['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
        
        if df.empty:
            return {"error": "No temperature data found in S3"}
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate summary statistics
        summary = {
            'total_records': len(df),
            'data_source': f"s3://{bucket_name}/{csv_key}",
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
            's3_info': bucket_info
        }
        
        print(f"📊 Temperature Summary (from S3):")
        print(f"   📈 Records: {summary['total_records']}")
        print(f"   🌡️ Current: {summary['temperature_stats']['current_celsius']}°C")
        print(f"   📊 Average: {summary['temperature_stats']['avg_celsius']}°C")
        print(f"   📉 Range: {summary['temperature_stats']['min_celsius']}°C - {summary['temperature_stats']['max_celsius']}°C")
        print(f"   ☁️ S3 Bucket: {bucket_name}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error generating S3 summary: {e}")
        return {"error": str(e)}


@flow(
    name="Campinas Temperature Monitor (S3)",
    description="Collects and stores temperature data for Campinas, SP in AWS S3",
    log_prints=True
)
def campinas_temperature_s3_pipeline():
    """
    Main temperature monitoring pipeline with S3 storage:
    1. Fetch current temperature data for Campinas
    2. Validate and clean the data
    3. Store in AWS S3 bucket (JSON + CSV formats)
    4. Generate summary statistics from S3 data
    """
    print("🚀 Starting Campinas Temperature Pipeline (S3 Storage)...")
    
    # Fetch temperature data
    temperature_data = get_campinas_temperature()
    
    # Validate data
    validated_data = validate_temperature_data(temperature_data)
    
    # Initialize S3 client
    s3_client = get_s3_client()
    
    # Load to S3 bucket
    bucket_info = load_to_s3_bucket(validated_data, s3_client)
    
    # Generate summary from S3
    summary = generate_s3_summary(s3_client, bucket_info)
    
    print("🎉 Campinas Temperature Pipeline (S3) completed!")
    
    return {
        'pipeline_status': 'completed',
        'temperature_celsius': validated_data['temperature_celsius'],
        'weather_description': validated_data['weather_description'],
        'storage_type': 's3',
        'bucket_info': bucket_info,
        'summary': summary,
        'execution_time': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running Campinas Temperature Pipeline (S3) locally...")
    
    # Check if AWS credentials are available
    if not (os.getenv('AWS_ACCESS_KEY_ID') or os.path.exists(os.path.expanduser('~/.aws/credentials'))):
        print("⚠️ AWS credentials not found. Please configure:")
        print("   export AWS_ACCESS_KEY_ID=your_access_key")
        print("   export AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("   export AWS_REGION=us-east-1")
        print("   export S3_BUCKET_NAME=your-bucket-name")
        exit(1)
    
    result = campinas_temperature_s3_pipeline()
    print(f"🎯 Pipeline result: {result['pipeline_status']}")
    print(f"🌡️ Current temperature: {result['temperature_celsius']}°C")
    print(f"🌤️ Weather: {result['weather_description']}")
    print(f"☁️ Stored in S3 bucket: {result['bucket_info']['bucket']}")

