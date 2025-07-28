"""
Example Data Pipeline with Prefect
Demonstrates a typical data lake ETL workflow
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def extract_sample_data():
    """Extract sample data from a public API"""
    print("🔍 Extracting sample data...")
    
    # Using JSONPlaceholder API for demo
    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    data = response.json()
    
    print(f"✅ Extracted {len(data)} records")
    return data


@task
def transform_data(raw_data):
    """Transform the raw data"""
    print("🔄 Transforming data...")
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_data)
    
    # Add some transformations
    df['title_length'] = df['title'].str.len()
    df['body_length'] = df['body'].str.len()
    df['created_at'] = datetime.now()
    df['word_count'] = df['body'].str.split().str.len()
    
    # Filter and clean
    df_clean = df[df['title_length'] > 10].copy()
    
    print(f"✅ Transformed data: {len(df_clean)} records after cleaning")
    return df_clean


@task
def load_data_to_lake(transformed_data):
    """Load data to our 'data lake' (simulated)"""
    print("💾 Loading data to lake...")
    
    # Simulate saving to different formats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON (raw zone)
    raw_path = f"/tmp/raw_posts_{timestamp}.json"
    transformed_data.to_json(raw_path, orient='records', indent=2)
    
    # Save as Parquet (processed zone)
    processed_path = f"/tmp/processed_posts_{timestamp}.parquet"
    transformed_data.to_parquet(processed_path)
    
    print(f"✅ Data saved to:")
    print(f"   📄 Raw: {raw_path}")
    print(f"   📊 Processed: {processed_path}")
    
    return {
        "raw_path": raw_path,
        "processed_path": processed_path,
        "record_count": len(transformed_data)
    }


@task
def generate_data_quality_report(data, load_result):
    """Generate a data quality report"""
    print("📊 Generating data quality report...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_records": len(data),
        "avg_title_length": data['title_length'].mean(),
        "avg_body_length": data['body_length'].mean(),
        "avg_word_count": data['word_count'].mean(),
        "files_created": [load_result["raw_path"], load_result["processed_path"]]
    }
    
    print("📈 Data Quality Report:")
    for key, value in report.items():
        if key != "files_created":
            print(f"   {key}: {value}")
    
    return report


@flow(name="Data Lake ETL Pipeline", description="Example ETL pipeline for data lake")
def data_lake_etl():
    """Main ETL flow for data lake"""
    print("🚀 Starting Data Lake ETL Pipeline...")
    
    # Extract
    raw_data = extract_sample_data()
    
    # Transform
    clean_data = transform_data(raw_data)
    
    # Load
    load_result = load_data_to_lake(clean_data)
    
    # Quality check
    quality_report = generate_data_quality_report(clean_data, load_result)
    
    print("🎉 Pipeline completed successfully!")
    return quality_report


@flow(name="Data Processing Workflow", description="Batch data processing")
def batch_processing_flow():
    """Example of batch processing workflow"""
    print("📦 Starting Batch Processing Workflow...")
    
    # Simulate multiple data sources
    sources = ["api_data", "file_data", "database_data"]
    
    results = []
    for source in sources:
        print(f"Processing {source}...")
        # In real scenario, each would have different extraction logic
        data = extract_sample_data()
        transformed = transform_data(data)
        result = load_data_to_lake(transformed)
        results.append(result)
    
    print(f"✅ Processed {len(results)} data sources")
    return results


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running flow locally for testing...")
    result = data_lake_etl()
    print(f"🎯 Final result: {result}")

