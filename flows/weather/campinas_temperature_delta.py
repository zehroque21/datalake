"""
Campinas Temperature Pipeline with Delta Lake
Collects temperature data and stores in Delta format for the raw layer
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from prefect import flow, task
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip


@task
def get_campinas_temperature() -> Dict[str, Any]:
    """Fetch current temperature data for Campinas, SP"""
    print("🌡️ Fetching temperature data for Campinas...")
    
    try:
        # Try to get real weather data
        response = requests.get(
            "https://wttr.in/Campinas,SP?format=j1",
            timeout=10,
            headers={'User-Agent': 'DataLake-Pipeline/1.0'}
        )
        
        if response.status_code == 200:
            weather_data = response.json()
            current = weather_data['current_condition'][0]
            
            # Extract relevant data
            data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'location': 'Campinas, SP, Brazil',
                'temperature_celsius': float(current['temp_C']),
                'temperature_fahrenheit': float(current['temp_F']),
                'humidity': int(current['humidity']),
                'weather_description': current['weatherDesc'][0]['value'],
                'wind_speed_kmh': float(current['windspeedKmph']),
                'wind_direction': current['winddir16Point'],
                'pressure_mb': float(current['pressure']),
                'feels_like_celsius': float(current['FeelsLikeC']),
                'uv_index': float(current['uvIndex']),
                'visibility_km': float(current['visibility']),
                'data_source': 'wttr.in',
                'data_quality_score': 100
            }
            
            print(f"✅ Temperature data collected:")
            print(f"   🌡️ Temperature: {data['temperature_celsius']}°C")
            print(f"   💧 Humidity: {data['humidity']}%")
            print(f"   🌤️ Weather: {data['weather_description']}")
            
            return data
            
    except Exception as e:
        print(f"⚠️ Error fetching real weather data: {e}")
    
    # Fallback to mock data
    print("🔄 Using mock temperature data...")
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'location': 'Campinas, SP, Brazil',
        'temperature_celsius': 22.5,
        'temperature_fahrenheit': 72.5,
        'humidity': 65,
        'weather_description': 'Partly cloudy',
        'wind_speed_kmh': 8.0,
        'wind_direction': 'SE',
        'pressure_mb': 1013.25,
        'feels_like_celsius': 24.0,
        'uv_index': 5.0,
        'visibility_km': 10.0,
        'data_source': 'mock_data',
        'data_quality_score': 75
    }


@task
def validate_temperature_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate temperature data quality"""
    print("🔍 Validating temperature data...")
    
    # Basic validation rules
    validations = {
        'temperature_range': -50 <= data['temperature_celsius'] <= 60,
        'humidity_range': 0 <= data['humidity'] <= 100,
        'pressure_range': 800 <= data['pressure_mb'] <= 1200,
        'wind_speed_positive': data['wind_speed_kmh'] >= 0,
        'uv_index_range': 0 <= data['uv_index'] <= 15,
        'visibility_positive': data['visibility_km'] >= 0
    }
    
    # Calculate quality score
    passed_validations = sum(validations.values())
    total_validations = len(validations)
    quality_score = (passed_validations / total_validations) * 100
    
    # Update quality score (minimum of original and validation score)
    data['data_quality_score'] = min(data['data_quality_score'], quality_score)
    data['validation_details'] = validations
    
    print(f"✅ Data validation completed (Quality Score: {quality_score}%)")
    return data


@task
def get_spark_session() -> SparkSession:
    """Create Spark session configured for Delta Lake"""
    print("⚡ Creating Spark session for Delta Lake...")
    
    builder = SparkSession.builder \
        .appName("CampinasTemperatureDelta") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.driver.memory", "1g") \
        .config("spark.executor.memory", "1g")
    
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    
    print("✅ Spark session created successfully")
    return spark


@task
def save_to_staging(data: Dict[str, Any]) -> str:
    """Save raw data to staging layer (JSON format)"""
    print("💾 Saving to staging layer...")
    
    staging_dir = "/app/s3/staging/weather"
    os.makedirs(staging_dir, exist_ok=True)
    
    staging_file = f"{staging_dir}/campinas_temperature_latest.json"
    
    with open(staging_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Data saved to staging: {staging_file}")
    return staging_file


@task
def save_to_delta_raw(spark: SparkSession, data: Dict[str, Any]) -> str:
    """Save validated data to raw layer as Delta table"""
    print("🗂️ Saving to Delta raw layer...")
    
    try:
        # Create DataFrame from data
        df = spark.createDataFrame([data])
        
        # Delta table path
        delta_path = "/app/s3/raw/weather/campinas_temperature_delta"
        
        # Write to Delta table (append mode for historical data)
        df.write \
            .format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .save(delta_path)
        
        print(f"✅ Data saved to Delta raw layer: {delta_path}")
        
        # Read back to verify and get record count
        delta_df = spark.read.format("delta").load(delta_path)
        record_count = delta_df.count()
        
        print(f"📊 Delta table now contains {record_count} records")
        
        return delta_path
        
    except Exception as e:
        print(f"❌ Error saving to Delta: {e}")
        raise


@task
def create_delta_metadata(spark: SparkSession, delta_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create metadata for the Delta table"""
    print("📋 Creating Delta table metadata...")
    
    try:
        # Read Delta table
        delta_df = spark.read.format("delta").load(delta_path)
        
        # Get table statistics
        record_count = delta_df.count()
        
        if record_count > 0:
            # Get temperature statistics
            temp_stats = delta_df.agg(
                {"temperature_celsius": "avg", "temperature_celsius": "min", "temperature_celsius": "max"}
            ).collect()[0]
            
            # Get date range
            date_stats = delta_df.agg(
                {"timestamp": "min", "timestamp": "max"}
            ).collect()[0]
            
            metadata = {
                'table_name': 'campinas_temperature_delta',
                'table_path': delta_path,
                'table_format': 'delta',
                'record_count': record_count,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'schema': [field.name for field in delta_df.schema.fields],
                'data_quality': {
                    'avg_quality_score': delta_df.agg({"data_quality_score": "avg"}).collect()[0][0],
                    'latest_quality_score': data['data_quality_score']
                },
                'temperature_stats': {
                    'avg_celsius': round(temp_stats[0], 2) if temp_stats[0] else None,
                    'min_celsius': temp_stats[1] if temp_stats[1] else None,
                    'max_celsius': temp_stats[2] if temp_stats[2] else None
                },
                'date_range': {
                    'first_record': date_stats[0],
                    'last_record': date_stats[1]
                },
                'data_lineage': {
                    'source_system': data['data_source'],
                    'pipeline': 'campinas_temperature_delta',
                    'layer': 'raw',
                    'format': 'delta'
                }
            }
        else:
            metadata = {
                'table_name': 'campinas_temperature_delta',
                'table_path': delta_path,
                'table_format': 'delta',
                'record_count': 0,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'error': 'No data found in Delta table'
            }
        
        # Save metadata
        metadata_path = "/app/s3/raw/weather/campinas_temperature_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Metadata created: {metadata_path}")
        print(f"📊 Table contains {record_count} records")
        
        return metadata
        
    except Exception as e:
        print(f"❌ Error creating metadata: {e}")
        return {'error': str(e)}


@flow(
    name="Campinas Temperature Delta Pipeline",
    description="Collect temperature data and store in Delta Lake format"
)
def campinas_temperature_delta_pipeline():
    """Main pipeline for collecting and storing temperature data in Delta Lake"""
    print("🚀 Starting Campinas Temperature Delta Pipeline...")
    
    try:
        # Step 1: Collect temperature data
        temperature_data = get_campinas_temperature()
        
        # Step 2: Validate data quality
        validated_data = validate_temperature_data(temperature_data)
        
        # Step 3: Save to staging (JSON)
        staging_file = save_to_staging(validated_data)
        
        # Step 4: Initialize Spark session
        spark = get_spark_session()
        
        # Step 5: Save to Delta raw layer
        delta_path = save_to_delta_raw(spark, validated_data)
        
        # Step 6: Create metadata
        metadata = create_delta_metadata(spark, delta_path, validated_data)
        
        # Step 7: Cleanup
        spark.stop()
        
        print("✅ Campinas Temperature Delta Pipeline completed successfully!")
        print(f"📄 Staging: {staging_file}")
        print(f"🗂️ Delta: {delta_path}")
        print(f"📋 Records: {metadata.get('record_count', 'unknown')}")
        
        return {
            'status': 'success',
            'staging_file': staging_file,
            'delta_path': delta_path,
            'metadata': metadata
        }
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    # Run the pipeline
    campinas_temperature_delta_pipeline()

