"""
AWS Integration Example with Prefect
Demonstrates integration with S3, Lambda, and other AWS services
"""

import boto3
import pandas as pd
from datetime import datetime
from prefect import flow, task
from prefect.blocks.system import Secret
import json


@task
def list_s3_buckets():
    """List S3 buckets (demo - requires AWS credentials)"""
    print("🪣 Listing S3 buckets...")
    
    try:
        # In production, use Prefect AWS blocks for credentials
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        print(f"✅ Found {len(buckets)} S3 buckets")
        return buckets
        
    except Exception as e:
        print(f"⚠️ AWS credentials not configured: {e}")
        # Return mock data for demo
        return ["demo-data-lake", "demo-processed", "demo-archive"]


@task
def simulate_s3_upload(data, bucket_name="demo-data-lake"):
    """Simulate uploading data to S3"""
    print(f"📤 Simulating upload to S3 bucket: {bucket_name}")
    
    # Convert data to JSON for upload
    if isinstance(data, pd.DataFrame):
        json_data = data.to_json(orient='records', indent=2)
    else:
        json_data = json.dumps(data, indent=2)
    
    # Simulate S3 key
    timestamp = datetime.now().strftime("%Y/%m/%d/%H%M%S")
    s3_key = f"raw-data/{timestamp}/data.json"
    
    print(f"✅ Simulated upload to s3://{bucket_name}/{s3_key}")
    print(f"📊 Data size: {len(json_data)} bytes")
    
    return {
        "bucket": bucket_name,
        "key": s3_key,
        "size_bytes": len(json_data),
        "upload_time": datetime.now().isoformat()
    }


@task
def trigger_lambda_function(s3_event):
    """Simulate triggering a Lambda function"""
    print("⚡ Simulating Lambda function trigger...")
    
    # Simulate Lambda payload
    lambda_payload = {
        "Records": [{
            "s3": {
                "bucket": {"name": s3_event["bucket"]},
                "object": {"key": s3_event["key"]}
            }
        }]
    }
    
    print(f"🔧 Lambda payload: {json.dumps(lambda_payload, indent=2)}")
    
    # Simulate processing result
    result = {
        "statusCode": 200,
        "body": {
            "message": "Data processed successfully",
            "processed_records": 100,
            "processing_time_ms": 1500
        }
    }
    
    print("✅ Lambda function executed successfully")
    return result


@task
def create_data_catalog_entry(s3_location, lambda_result):
    """Create entry in data catalog (simulated)"""
    print("📚 Creating data catalog entry...")
    
    catalog_entry = {
        "table_name": "processed_data",
        "location": f"s3://{s3_location['bucket']}/{s3_location['key']}",
        "format": "JSON",
        "schema": {
            "id": "bigint",
            "title": "string",
            "body": "string",
            "title_length": "int",
            "created_at": "timestamp"
        },
        "partitions": ["year", "month", "day"],
        "created_at": datetime.now().isoformat(),
        "records_processed": lambda_result["body"]["processed_records"]
    }
    
    print("✅ Data catalog entry created:")
    print(f"   📋 Table: {catalog_entry['table_name']}")
    print(f"   📍 Location: {catalog_entry['location']}")
    print(f"   📊 Records: {catalog_entry['records_processed']}")
    
    return catalog_entry


@flow(name="AWS Data Lake Integration", description="AWS services integration example")
def aws_data_lake_flow():
    """Demonstrate AWS integration workflow"""
    print("☁️ Starting AWS Data Lake Integration Flow...")
    
    # List available buckets
    buckets = list_s3_buckets()
    
    # Create sample data
    sample_data = pd.DataFrame({
        'id': range(1, 101),
        'title': [f'Sample Title {i}' for i in range(1, 101)],
        'body': [f'Sample content for record {i}' for i in range(1, 101)],
        'created_at': [datetime.now().isoformat() for _ in range(100)]
    })
    
    # Upload to S3 (simulated)
    s3_result = simulate_s3_upload(sample_data, buckets[0] if buckets else "demo-bucket")
    
    # Trigger Lambda processing
    lambda_result = trigger_lambda_function(s3_result)
    
    # Update data catalog
    catalog_entry = create_data_catalog_entry(s3_result, lambda_result)
    
    print("🎉 AWS integration workflow completed!")
    
    return {
        "s3_upload": s3_result,
        "lambda_execution": lambda_result,
        "catalog_entry": catalog_entry
    }


@flow(name="Multi-Environment Deployment", description="Deploy across environments")
def multi_env_deployment():
    """Example of multi-environment deployment"""
    environments = ["dev", "staging", "prod"]
    
    results = {}
    for env in environments:
        print(f"🚀 Deploying to {env} environment...")
        
        # Simulate environment-specific configuration
        config = {
            "env": env,
            "bucket_prefix": f"{env}-data-lake",
            "lambda_memory": 512 if env == "prod" else 256,
            "retention_days": 365 if env == "prod" else 30
        }
        
        print(f"⚙️ Environment config: {config}")
        results[env] = config
    
    return results


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running AWS integration flow locally...")
    result = aws_data_lake_flow()
    print(f"🎯 Final result: {result}")

