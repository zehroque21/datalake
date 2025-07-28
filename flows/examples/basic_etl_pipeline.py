"""
Basic ETL Pipeline Example
A simple extract, transform, load workflow demonstrating Prefect fundamentals
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
import os


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def extract_data_from_api(api_url: str = "https://jsonplaceholder.typicode.com/posts"):
    """Extract data from a REST API"""
    print(f"🔍 Extracting data from: {api_url}")
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Successfully extracted {len(data)} records")
        return data
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        raise


@task
def transform_data(raw_data: list) -> pd.DataFrame:
    """Transform raw data into a clean DataFrame"""
    print("🔄 Transforming data...")
    
    if not raw_data:
        print("⚠️ No data to transform")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_data)
    
    # Add computed columns
    df['title_length'] = df['title'].str.len()
    df['body_length'] = df['body'].str.len()
    df['word_count'] = df['body'].str.split().str.len()
    df['processed_at'] = datetime.now()
    
    # Data quality checks
    df = df.dropna()  # Remove null values
    df = df[df['title_length'] > 0]  # Remove empty titles
    
    # Add data quality metrics
    df['quality_score'] = (
        (df['title_length'] > 10).astype(int) +
        (df['body_length'] > 50).astype(int) +
        (df['word_count'] > 10).astype(int)
    ) / 3
    
    print(f"✅ Transformed data: {len(df)} records after cleaning")
    print(f"📊 Average quality score: {df['quality_score'].mean():.2f}")
    
    return df


@task
def load_data_to_storage(df: pd.DataFrame, output_dir: str = "/tmp/datalake") -> dict:
    """Load transformed data to storage"""
    print("💾 Loading data to storage...")
    
    if df.empty:
        print("⚠️ No data to load")
        return {"status": "no_data", "files": []}
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save in multiple formats
    files_created = []
    
    # 1. JSON format (raw zone)
    json_path = f"{output_dir}/posts_raw_{timestamp}.json"
    df.to_json(json_path, orient='records', indent=2)
    files_created.append(json_path)
    
    # 2. Parquet format (processed zone)
    parquet_path = f"{output_dir}/posts_processed_{timestamp}.parquet"
    df.to_parquet(parquet_path, index=False)
    files_created.append(parquet_path)
    
    # 3. CSV format (for analysis)
    csv_path = f"{output_dir}/posts_analysis_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    files_created.append(csv_path)
    
    # Create summary statistics
    summary = {
        "total_records": len(df),
        "avg_title_length": df['title_length'].mean(),
        "avg_body_length": df['body_length'].mean(),
        "avg_word_count": df['word_count'].mean(),
        "avg_quality_score": df['quality_score'].mean(),
        "high_quality_records": len(df[df['quality_score'] > 0.7]),
        "processed_at": datetime.now().isoformat()
    }
    
    # Save summary
    summary_path = f"{output_dir}/summary_{timestamp}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    files_created.append(summary_path)
    
    print(f"✅ Data loaded successfully:")
    for file_path in files_created:
        print(f"   📄 {file_path}")
    
    return {
        "status": "success",
        "files": files_created,
        "summary": summary
    }


@task
def generate_data_quality_report(summary: dict) -> dict:
    """Generate a data quality report"""
    print("📊 Generating data quality report...")
    
    if not summary or summary.get("status") != "success":
        return {"status": "no_data"}
    
    data_summary = summary["summary"]
    
    # Quality thresholds
    quality_report = {
        "timestamp": datetime.now().isoformat(),
        "total_records": data_summary["total_records"],
        "quality_metrics": {
            "avg_title_length": {
                "value": data_summary["avg_title_length"],
                "status": "good" if data_summary["avg_title_length"] > 20 else "warning"
            },
            "avg_body_length": {
                "value": data_summary["avg_body_length"],
                "status": "good" if data_summary["avg_body_length"] > 100 else "warning"
            },
            "avg_quality_score": {
                "value": data_summary["avg_quality_score"],
                "status": "good" if data_summary["avg_quality_score"] > 0.6 else "warning"
            },
            "high_quality_percentage": {
                "value": (data_summary["high_quality_records"] / data_summary["total_records"]) * 100,
                "status": "good" if (data_summary["high_quality_records"] / data_summary["total_records"]) > 0.5 else "warning"
            }
        },
        "recommendations": []
    }
    
    # Add recommendations based on quality metrics
    if quality_report["quality_metrics"]["avg_title_length"]["status"] == "warning":
        quality_report["recommendations"].append("Consider filtering out posts with very short titles")
    
    if quality_report["quality_metrics"]["avg_body_length"]["status"] == "warning":
        quality_report["recommendations"].append("Review posts with short body content for relevance")
    
    if quality_report["quality_metrics"]["avg_quality_score"]["status"] == "warning":
        quality_report["recommendations"].append("Implement additional data quality checks")
    
    print("📈 Data Quality Report:")
    print(f"   📊 Total records: {quality_report['total_records']}")
    print(f"   ⭐ Average quality score: {data_summary['avg_quality_score']:.2f}")
    print(f"   🎯 High quality records: {data_summary['high_quality_records']}")
    
    return quality_report


@flow(name="Basic ETL Pipeline", description="Extract data from API, transform, and load to storage")
def basic_etl_pipeline(
    api_url: str = "https://jsonplaceholder.typicode.com/posts",
    output_dir: str = "/tmp/datalake"
):
    """
    Main ETL flow that demonstrates:
    1. Data extraction from REST API
    2. Data transformation and quality checks
    3. Data loading in multiple formats
    4. Quality reporting
    """
    print("🚀 Starting Basic ETL Pipeline...")
    
    # Extract
    raw_data = extract_data_from_api(api_url)
    
    # Transform
    clean_data = transform_data(raw_data)
    
    # Load
    load_result = load_data_to_storage(clean_data, output_dir)
    
    # Quality Report
    quality_report = generate_data_quality_report(load_result)
    
    print("🎉 ETL Pipeline completed successfully!")
    
    return {
        "pipeline_status": "completed",
        "load_result": load_result,
        "quality_report": quality_report,
        "execution_time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running Basic ETL Pipeline locally...")
    result = basic_etl_pipeline()
    print(f"🎯 Pipeline result: {result['pipeline_status']}")
    print(f"📊 Files created: {len(result['load_result'].get('files', []))}")

