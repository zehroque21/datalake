"""
Data Quality Monitoring Pipeline
Monitors data quality across the data lake and sends alerts
"""

import pandas as pd
import boto3
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
import numpy as np
from typing import Dict, List, Any


@task
def scan_s3_data_sources(bucket_name: str, prefixes: List[str] = None) -> Dict[str, Any]:
    """Scan S3 bucket for data sources and their metadata"""
    print(f"🔍 Scanning S3 data sources in bucket: {bucket_name}")
    
    if prefixes is None:
        prefixes = ["raw/", "processed/", "delta/"]
    
    try:
        s3_client = boto3.client('s3')
        data_sources = {}
        
        for prefix in prefixes:
            print(f"📂 Scanning prefix: {prefix}")
            
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                continue
            
            files = []
            total_size = 0
            latest_modified = None
            
            for obj in response['Contents']:
                file_info = {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag']
                }
                files.append(file_info)
                total_size += obj['Size']
                
                if latest_modified is None or obj['LastModified'] > latest_modified:
                    latest_modified = obj['LastModified']
            
            data_sources[prefix] = {
                'file_count': len(files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'latest_modified': latest_modified.isoformat() if latest_modified else None,
                'files': files[:10]  # Keep only first 10 for brevity
            }
        
        print(f"✅ Scanned {len(data_sources)} data source prefixes")
        return data_sources
        
    except Exception as e:
        print(f"❌ Error scanning S3: {e}")
        raise


@task
def check_data_freshness(data_sources: Dict[str, Any], max_age_hours: int = 24) -> Dict[str, Any]:
    """Check if data sources are fresh (updated recently)"""
    print(f"⏰ Checking data freshness (max age: {max_age_hours} hours)")
    
    freshness_report = {
        'check_time': datetime.now().isoformat(),
        'max_age_hours': max_age_hours,
        'sources': {},
        'alerts': []
    }
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    for prefix, source_info in data_sources.items():
        if source_info['latest_modified']:
            latest_modified = datetime.fromisoformat(source_info['latest_modified'].replace('Z', '+00:00'))
            latest_modified = latest_modified.replace(tzinfo=None)  # Remove timezone for comparison
            
            is_fresh = latest_modified > cutoff_time
            age_hours = (datetime.now() - latest_modified).total_seconds() / 3600
            
            freshness_report['sources'][prefix] = {
                'latest_modified': source_info['latest_modified'],
                'age_hours': round(age_hours, 2),
                'is_fresh': is_fresh,
                'file_count': source_info['file_count']
            }
            
            if not is_fresh:
                alert = {
                    'type': 'data_freshness',
                    'severity': 'warning' if age_hours < 48 else 'critical',
                    'source': prefix,
                    'message': f"Data in {prefix} is {age_hours:.1f} hours old (max: {max_age_hours})",
                    'age_hours': age_hours
                }
                freshness_report['alerts'].append(alert)
                print(f"⚠️ {alert['message']}")
        else:
            freshness_report['sources'][prefix] = {
                'latest_modified': None,
                'age_hours': None,
                'is_fresh': False,
                'file_count': source_info['file_count']
            }
            
            alert = {
                'type': 'data_freshness',
                'severity': 'critical',
                'source': prefix,
                'message': f"No files found in {prefix}",
                'age_hours': None
            }
            freshness_report['alerts'].append(alert)
            print(f"🚨 {alert['message']}")
    
    print(f"✅ Freshness check completed. Found {len(freshness_report['alerts'])} alerts")
    return freshness_report


@task
def check_data_volume_anomalies(data_sources: Dict[str, Any]) -> Dict[str, Any]:
    """Check for unusual data volumes (too much or too little data)"""
    print("📊 Checking for data volume anomalies")
    
    volume_report = {
        'check_time': datetime.now().isoformat(),
        'sources': {},
        'alerts': []
    }
    
    # Define expected volume ranges (in MB)
    expected_volumes = {
        'raw/': {'min': 1, 'max': 1000},
        'processed/': {'min': 0.5, 'max': 500},
        'delta/': {'min': 0.5, 'max': 500}
    }
    
    for prefix, source_info in data_sources.items():
        size_mb = source_info['total_size_mb']
        file_count = source_info['file_count']
        
        volume_report['sources'][prefix] = {
            'size_mb': size_mb,
            'file_count': file_count,
            'status': 'normal'
        }
        
        # Check against expected volumes
        if prefix in expected_volumes:
            expected = expected_volumes[prefix]
            
            if size_mb < expected['min']:
                alert = {
                    'type': 'data_volume',
                    'severity': 'warning',
                    'source': prefix,
                    'message': f"Low data volume in {prefix}: {size_mb}MB (expected min: {expected['min']}MB)",
                    'actual_mb': size_mb,
                    'expected_min_mb': expected['min']
                }
                volume_report['alerts'].append(alert)
                volume_report['sources'][prefix]['status'] = 'low_volume'
                print(f"⚠️ {alert['message']}")
                
            elif size_mb > expected['max']:
                alert = {
                    'type': 'data_volume',
                    'severity': 'warning',
                    'source': prefix,
                    'message': f"High data volume in {prefix}: {size_mb}MB (expected max: {expected['max']}MB)",
                    'actual_mb': size_mb,
                    'expected_max_mb': expected['max']
                }
                volume_report['alerts'].append(alert)
                volume_report['sources'][prefix]['status'] = 'high_volume'
                print(f"⚠️ {alert['message']}")
        
        # Check for empty directories
        if file_count == 0:
            alert = {
                'type': 'data_volume',
                'severity': 'critical',
                'source': prefix,
                'message': f"No files found in {prefix}",
                'actual_mb': size_mb,
                'file_count': file_count
            }
            volume_report['alerts'].append(alert)
            volume_report['sources'][prefix]['status'] = 'empty'
            print(f"🚨 {alert['message']}")
    
    print(f"✅ Volume check completed. Found {len(volume_report['alerts'])} alerts")
    return volume_report


@task
def sample_data_quality_check(bucket_name: str, sample_files: int = 3) -> Dict[str, Any]:
    """Sample a few files and check their data quality"""
    print(f"🔬 Performing data quality check on {sample_files} sample files")
    
    try:
        s3_client = boto3.client('s3')
        
        # Get sample files from processed data
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix="processed/",
            MaxKeys=sample_files
        )
        
        if 'Contents' not in response:
            return {
                'status': 'no_data',
                'message': 'No processed files found for quality check'
            }
        
        quality_report = {
            'check_time': datetime.now().isoformat(),
            'files_checked': 0,
            'total_records': 0,
            'quality_metrics': {},
            'alerts': []
        }
        
        for obj in response['Contents'][:sample_files]:
            key = obj['Key']
            
            if not (key.endswith('.json') or key.endswith('.csv') or key.endswith('.parquet')):
                continue
            
            try:
                print(f"📄 Checking file: {key}")
                
                # Get file content
                file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
                
                if key.endswith('.json'):
                    content = file_obj['Body'].read().decode('utf-8')
                    data = json.loads(content)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
                        
                elif key.endswith('.csv'):
                    content = file_obj['Body'].read().decode('utf-8')
                    df = pd.read_csv(pd.io.common.StringIO(content))
                    
                elif key.endswith('.parquet'):
                    # For parquet, we'd need pyarrow, skip for now
                    continue
                
                # Perform quality checks
                record_count = len(df)
                null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                duplicate_percentage = (df.duplicated().sum() / len(df)) * 100
                
                file_quality = {
                    'file': key,
                    'record_count': record_count,
                    'column_count': len(df.columns),
                    'null_percentage': round(null_percentage, 2),
                    'duplicate_percentage': round(duplicate_percentage, 2),
                    'columns': list(df.columns)
                }
                
                quality_report['files_checked'] += 1
                quality_report['total_records'] += record_count
                quality_report['quality_metrics'][key] = file_quality
                
                # Check for quality issues
                if null_percentage > 20:
                    alert = {
                        'type': 'data_quality',
                        'severity': 'warning',
                        'source': key,
                        'message': f"High null percentage in {key}: {null_percentage:.1f}%",
                        'null_percentage': null_percentage
                    }
                    quality_report['alerts'].append(alert)
                    print(f"⚠️ {alert['message']}")
                
                if duplicate_percentage > 10:
                    alert = {
                        'type': 'data_quality',
                        'severity': 'warning',
                        'source': key,
                        'message': f"High duplicate percentage in {key}: {duplicate_percentage:.1f}%",
                        'duplicate_percentage': duplicate_percentage
                    }
                    quality_report['alerts'].append(alert)
                    print(f"⚠️ {alert['message']}")
                
                print(f"✅ Quality check completed for {key}: {record_count} records, {null_percentage:.1f}% nulls")
                
            except Exception as e:
                print(f"⚠️ Error checking file {key}: {e}")
                continue
        
        print(f"✅ Data quality check completed. Checked {quality_report['files_checked']} files")
        return quality_report
        
    except Exception as e:
        print(f"❌ Error in data quality check: {e}")
        raise


@task
def generate_monitoring_summary(
    freshness_report: Dict[str, Any],
    volume_report: Dict[str, Any],
    quality_report: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate a comprehensive monitoring summary"""
    print("📋 Generating monitoring summary...")
    
    # Collect all alerts
    all_alerts = []
    all_alerts.extend(freshness_report.get('alerts', []))
    all_alerts.extend(volume_report.get('alerts', []))
    all_alerts.extend(quality_report.get('alerts', []))
    
    # Categorize alerts by severity
    critical_alerts = [a for a in all_alerts if a.get('severity') == 'critical']
    warning_alerts = [a for a in all_alerts if a.get('severity') == 'warning']
    
    # Calculate overall health score
    total_checks = len(freshness_report.get('sources', {})) + len(volume_report.get('sources', {})) + quality_report.get('files_checked', 0)
    total_issues = len(all_alerts)
    health_score = max(0, 100 - (total_issues / max(total_checks, 1)) * 100) if total_checks > 0 else 0
    
    summary = {
        'monitoring_timestamp': datetime.now().isoformat(),
        'overall_health_score': round(health_score, 1),
        'status': 'healthy' if health_score > 80 else 'warning' if health_score > 60 else 'critical',
        'total_alerts': len(all_alerts),
        'critical_alerts': len(critical_alerts),
        'warning_alerts': len(warning_alerts),
        'checks_performed': {
            'freshness_sources': len(freshness_report.get('sources', {})),
            'volume_sources': len(volume_report.get('sources', {})),
            'quality_files': quality_report.get('files_checked', 0),
            'total_records_checked': quality_report.get('total_records', 0)
        },
        'alerts_by_type': {
            'data_freshness': len([a for a in all_alerts if a.get('type') == 'data_freshness']),
            'data_volume': len([a for a in all_alerts if a.get('type') == 'data_volume']),
            'data_quality': len([a for a in all_alerts if a.get('type') == 'data_quality'])
        },
        'recommendations': []
    }
    
    # Add recommendations based on alerts
    if critical_alerts:
        summary['recommendations'].append("🚨 Address critical alerts immediately - data pipeline may be broken")
    
    if len([a for a in all_alerts if a.get('type') == 'data_freshness']) > 0:
        summary['recommendations'].append("⏰ Check data ingestion processes - some sources are stale")
    
    if len([a for a in all_alerts if a.get('type') == 'data_volume']) > 0:
        summary['recommendations'].append("📊 Review data volume patterns - unusual activity detected")
    
    if len([a for a in all_alerts if a.get('type') == 'data_quality']) > 0:
        summary['recommendations'].append("🔍 Investigate data quality issues - high nulls or duplicates found")
    
    if not summary['recommendations']:
        summary['recommendations'].append("✅ All checks passed - data lake is healthy")
    
    print(f"📊 Monitoring Summary:")
    print(f"   🎯 Health Score: {summary['overall_health_score']}%")
    print(f"   🚨 Total Alerts: {summary['total_alerts']}")
    print(f"   📈 Status: {summary['status'].upper()}")
    
    return summary


@flow(name="Data Quality Monitor", description="Comprehensive data quality monitoring for the data lake")
def data_quality_monitor(
    bucket_name: str = "datalake-bucket-for-prefect-and-delta-v2",
    max_age_hours: int = 24,
    sample_files: int = 3
):
    """
    Data Quality Monitoring Pipeline:
    1. Scan S3 data sources
    2. Check data freshness
    3. Check data volume anomalies
    4. Sample data quality checks
    5. Generate comprehensive summary
    """
    print("🚀 Starting Data Quality Monitoring...")
    
    # Scan data sources
    data_sources = scan_s3_data_sources(bucket_name)
    
    # Check freshness
    freshness_report = check_data_freshness(data_sources, max_age_hours)
    
    # Check volume anomalies
    volume_report = check_data_volume_anomalies(data_sources)
    
    # Sample quality check
    quality_report = sample_data_quality_check(bucket_name, sample_files)
    
    # Generate summary
    monitoring_summary = generate_monitoring_summary(
        freshness_report, volume_report, quality_report
    )
    
    print("🎉 Data Quality Monitoring completed!")
    
    return {
        'monitoring_summary': monitoring_summary,
        'freshness_report': freshness_report,
        'volume_report': volume_report,
        'quality_report': quality_report,
        'execution_time': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running Data Quality Monitor locally...")
    
    try:
        result = data_quality_monitor()
        print(f"🎯 Monitoring result: {result['monitoring_summary']['status']}")
        print(f"📊 Health score: {result['monitoring_summary']['overall_health_score']}%")
        print(f"🚨 Total alerts: {result['monitoring_summary']['total_alerts']}")
    except Exception as e:
        print(f"⚠️ Monitoring failed (expected in local environment without AWS setup): {e}")
        print("💡 This monitor is designed to run in the AWS environment with proper credentials")

