"""
S3 Data Pipeline
ETL pipeline that works with AWS S3 for data lake operations
"""

import pandas as pd
import boto3
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
import os
from io import StringIO, BytesIO


@task
def extract_from_s3(bucket_name: str, key_prefix: str = "raw/") -> list:
    """Extract data files from S3 bucket"""
    print(f"🔍 Extracting data from S3: s3://{bucket_name}/{key_prefix}")
    
    try:
        s3_client = boto3.client('s3')
        
        # List objects in the bucket with the given prefix
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=key_prefix
        )
        
        if 'Contents' not in response:
            print("⚠️ No files found in S3 bucket")
            return []
        
        files_data = []
        
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.json') or key.endswith('.csv'):
                print(f"📄 Reading file: {key}")
                
                # Get object from S3
                file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
                file_content = file_obj['Body'].read().decode('utf-8')
                
                files_data.append({
                    'key': key,
                    'content': file_content,
                    'last_modified': obj['LastModified'].isoformat(),
                    'size': obj['Size']
                })
        
        print(f"✅ Successfully extracted {len(files_data)} files from S3")
        return files_data
        
    except Exception as e:
        print(f"❌ Error extracting from S3: {e}")
        raise


@task
def transform_s3_data(files_data: list) -> pd.DataFrame:
    """Transform data from S3 files"""
    print("🔄 Transforming S3 data...")
    
    if not files_data:
        print("⚠️ No data to transform")
        return pd.DataFrame()
    
    all_dataframes = []
    
    for file_data in files_data:
        key = file_data['key']
        content = file_data['content']
        
        try:
            if key.endswith('.json'):
                # Parse JSON data
                json_data = json.loads(content)
                if isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                else:
                    df = pd.DataFrame([json_data])
            
            elif key.endswith('.csv'):
                # Parse CSV data
                df = pd.read_csv(StringIO(content))
            
            else:
                continue
            
            # Add metadata columns
            df['source_file'] = key
            df['file_last_modified'] = file_data['last_modified']
            df['file_size'] = file_data['size']
            df['processed_at'] = datetime.now()
            
            all_dataframes.append(df)
            print(f"✅ Processed {key}: {len(df)} records")
            
        except Exception as e:
            print(f"⚠️ Error processing {key}: {e}")
            continue
    
    if not all_dataframes:
        print("⚠️ No valid data found in files")
        return pd.DataFrame()
    
    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    
    # Data quality improvements
    combined_df = combined_df.drop_duplicates()
    combined_df = combined_df.dropna(how='all')
    
    print(f"✅ Combined data: {len(combined_df)} total records")
    return combined_df


@task
def load_to_s3_delta_lake(
    df: pd.DataFrame, 
    bucket_name: str, 
    table_name: str = "processed_data"
) -> dict:
    """Load data to S3 in Delta Lake format (Parquet for now)"""
    print(f"💾 Loading data to S3 Delta Lake: s3://{bucket_name}/delta/{table_name}/")
    
    if df.empty:
        print("⚠️ No data to load")
        return {"status": "no_data"}
    
    try:
        s3_client = boto3.client('s3')
        
        # Generate partition path based on current date
        current_date = datetime.now()
        partition_path = f"delta/{table_name}/year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/"
        
        # Generate unique filename
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        filename = f"data_{timestamp}.parquet"
        s3_key = f"{partition_path}{filename}"
        
        # Convert DataFrame to Parquet
        parquet_buffer = BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
        parquet_buffer.seek(0)
        
        # Upload to S3
        s3_client.upload_fileobj(
            parquet_buffer,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': 'application/octet-stream',
                'Metadata': {
                    'table_name': table_name,
                    'record_count': str(len(df)),
                    'processed_at': current_date.isoformat(),
                    'format': 'parquet'
                }
            }
        )
        
        # Create/update table metadata
        metadata = {
            "table_name": table_name,
            "location": f"s3://{bucket_name}/{partition_path}",
            "format": "parquet",
            "partitions": {
                "year": current_date.year,
                "month": current_date.month,
                "day": current_date.day
            },
            "schema": list(df.columns),
            "record_count": len(df),
            "last_updated": current_date.isoformat(),
            "files": [s3_key]
        }
        
        # Save metadata
        metadata_key = f"delta/{table_name}/_metadata/metadata_{timestamp}.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        print(f"✅ Data loaded successfully:")
        print(f"   📄 Data file: s3://{bucket_name}/{s3_key}")
        print(f"   📋 Metadata: s3://{bucket_name}/{metadata_key}")
        print(f"   📊 Records: {len(df)}")
        
        return {
            "status": "success",
            "s3_key": s3_key,
            "metadata_key": metadata_key,
            "record_count": len(df),
            "table_name": table_name,
            "partition_path": partition_path
        }
        
    except Exception as e:
        print(f"❌ Error loading to S3: {e}")
        raise


@task
def create_data_catalog_entry(load_result: dict, bucket_name: str) -> dict:
    """Create or update AWS Glue Data Catalog entry"""
    print("📚 Creating/updating Data Catalog entry...")
    
    if load_result.get("status") != "success":
        print("⚠️ No successful load to catalog")
        return {"status": "skipped"}
    
    try:
        glue_client = boto3.client('glue')
        
        table_name = load_result["table_name"]
        database_name = "datalake_db"  # Default database
        
        # Table definition
        table_input = {
            'Name': table_name,
            'StorageDescriptor': {
                'Columns': [
                    {'Name': 'id', 'Type': 'bigint'},
                    {'Name': 'title', 'Type': 'string'},
                    {'Name': 'body', 'Type': 'string'},
                    {'Name': 'userId', 'Type': 'bigint'},
                    {'Name': 'source_file', 'Type': 'string'},
                    {'Name': 'file_last_modified', 'Type': 'string'},
                    {'Name': 'file_size', 'Type': 'bigint'},
                    {'Name': 'processed_at', 'Type': 'timestamp'}
                ],
                'Location': f"s3://{bucket_name}/delta/{table_name}/",
                'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                'SerdeInfo': {
                    'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                }
            },
            'PartitionKeys': [
                {'Name': 'year', 'Type': 'int'},
                {'Name': 'month', 'Type': 'int'},
                {'Name': 'day', 'Type': 'int'}
            ],
            'TableType': 'EXTERNAL_TABLE',
            'Parameters': {
                'classification': 'parquet',
                'compressionType': 'snappy',
                'typeOfData': 'file'
            }
        }
        
        # Try to update existing table, create if doesn't exist
        try:
            glue_client.update_table(
                DatabaseName=database_name,
                TableInput=table_input
            )
            print(f"✅ Updated existing table: {table_name}")
            
        except glue_client.exceptions.EntityNotFoundException:
            glue_client.create_table(
                DatabaseName=database_name,
                TableInput=table_input
            )
            print(f"✅ Created new table: {table_name}")
        
        return {
            "status": "success",
            "database": database_name,
            "table": table_name,
            "location": f"s3://{bucket_name}/delta/{table_name}/"
        }
        
    except Exception as e:
        print(f"⚠️ Error with Data Catalog (continuing anyway): {e}")
        return {"status": "error", "error": str(e)}


@flow(name="S3 Data Pipeline", description="ETL pipeline for S3 data lake operations")
def s3_data_pipeline(
    bucket_name: str = "datalake-bucket-for-prefect-and-delta-v2",
    input_prefix: str = "raw/",
    table_name: str = "processed_posts"
):
    """
    S3 Data Lake ETL Pipeline:
    1. Extract data from S3 raw zone
    2. Transform and clean data
    3. Load to S3 delta lake (partitioned parquet)
    4. Update AWS Glue Data Catalog
    """
    print("🚀 Starting S3 Data Pipeline...")
    
    # Extract from S3
    files_data = extract_from_s3(bucket_name, input_prefix)
    
    # Transform data
    clean_data = transform_s3_data(files_data)
    
    # Load to Delta Lake format
    load_result = load_to_s3_delta_lake(clean_data, bucket_name, table_name)
    
    # Update Data Catalog
    catalog_result = create_data_catalog_entry(load_result, bucket_name)
    
    print("🎉 S3 Data Pipeline completed!")
    
    return {
        "pipeline_status": "completed",
        "files_processed": len(files_data),
        "records_processed": len(clean_data) if not clean_data.empty else 0,
        "load_result": load_result,
        "catalog_result": catalog_result,
        "execution_time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running S3 Data Pipeline locally...")
    
    # Note: This requires AWS credentials and S3 bucket access
    # For local testing, you might want to use mock data
    try:
        result = s3_data_pipeline()
        print(f"🎯 Pipeline result: {result['pipeline_status']}")
        print(f"📊 Records processed: {result['records_processed']}")
    except Exception as e:
        print(f"⚠️ Pipeline failed (expected in local environment without AWS setup): {e}")
        print("💡 This pipeline is designed to run in the AWS environment with proper credentials")

