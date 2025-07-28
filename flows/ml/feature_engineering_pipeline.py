"""
Feature Engineering Pipeline for Machine Learning
Prepares features from raw data for ML model training and inference
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
import json
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from typing import Dict, List, Tuple, Any


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def load_raw_data(data_source: str = "/tmp/datalake") -> pd.DataFrame:
    """Load raw data for feature engineering"""
    print(f"📥 Loading raw data from: {data_source}")
    
    try:
        # For demo purposes, we'll create sample data
        # In production, this would load from S3, database, etc.
        
        # Generate sample data that mimics real-world scenarios
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'id': range(1, n_samples + 1),
            'title': [f"Sample title {i} with various content" for i in range(n_samples)],
            'body': [f"This is body content {i} with different lengths and patterns. " * np.random.randint(1, 10) for i in range(n_samples)],
            'category': np.random.choice(['tech', 'business', 'science', 'sports', 'entertainment'], n_samples),
            'author_id': np.random.randint(1, 100, n_samples),
            'publish_date': pd.date_range(start='2024-01-01', periods=n_samples, freq='H'),
            'view_count': np.random.exponential(100, n_samples).astype(int),
            'like_count': np.random.poisson(10, n_samples),
            'comment_count': np.random.poisson(5, n_samples),
            'is_featured': np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
            'reading_time_minutes': np.random.normal(5, 2, n_samples).clip(1, 30)
        }
        
        df = pd.DataFrame(data)
        
        print(f"✅ Loaded {len(df)} records for feature engineering")
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise


@task
def create_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features from text columns"""
    print("📝 Creating text features...")
    
    df_features = df.copy()
    
    # Basic text statistics
    df_features['title_length'] = df_features['title'].str.len()
    df_features['title_word_count'] = df_features['title'].str.split().str.len()
    df_features['body_length'] = df_features['body'].str.len()
    df_features['body_word_count'] = df_features['body'].str.split().str.len()
    
    # Text complexity features
    df_features['avg_word_length_title'] = df_features['title'].apply(
        lambda x: np.mean([len(word) for word in x.split()]) if x.split() else 0
    )
    df_features['avg_word_length_body'] = df_features['body'].apply(
        lambda x: np.mean([len(word) for word in x.split()]) if x.split() else 0
    )
    
    # Punctuation and special characters
    df_features['title_punctuation_count'] = df_features['title'].apply(
        lambda x: len(re.findall(r'[^\w\s]', x))
    )
    df_features['body_punctuation_count'] = df_features['body'].apply(
        lambda x: len(re.findall(r'[^\w\s]', x))
    )
    
    # Uppercase ratio
    df_features['title_uppercase_ratio'] = df_features['title'].apply(
        lambda x: sum(1 for c in x if c.isupper()) / len(x) if len(x) > 0 else 0
    )
    
    # Question marks and exclamation marks (engagement indicators)
    df_features['title_has_question'] = df_features['title'].str.contains(r'\?').astype(int)
    df_features['title_has_exclamation'] = df_features['title'].str.contains(r'!').astype(int)
    
    # Readability approximation (simple version)
    df_features['readability_score'] = (
        df_features['body_word_count'] / df_features['reading_time_minutes']
    ).fillna(0)
    
    print(f"✅ Created {len([col for col in df_features.columns if col not in df.columns])} text features")
    return df_features


@task
def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features from datetime columns"""
    print("⏰ Creating temporal features...")
    
    df_features = df.copy()
    
    # Ensure publish_date is datetime
    df_features['publish_date'] = pd.to_datetime(df_features['publish_date'])
    
    # Basic temporal features
    df_features['publish_hour'] = df_features['publish_date'].dt.hour
    df_features['publish_day_of_week'] = df_features['publish_date'].dt.dayofweek
    df_features['publish_month'] = df_features['publish_date'].dt.month
    df_features['publish_quarter'] = df_features['publish_date'].dt.quarter
    
    # Cyclical encoding for temporal features
    df_features['hour_sin'] = np.sin(2 * np.pi * df_features['publish_hour'] / 24)
    df_features['hour_cos'] = np.cos(2 * np.pi * df_features['publish_hour'] / 24)
    df_features['day_sin'] = np.sin(2 * np.pi * df_features['publish_day_of_week'] / 7)
    df_features['day_cos'] = np.cos(2 * np.pi * df_features['publish_day_of_week'] / 7)
    df_features['month_sin'] = np.sin(2 * np.pi * df_features['publish_month'] / 12)
    df_features['month_cos'] = np.cos(2 * np.pi * df_features['publish_month'] / 12)
    
    # Time-based flags
    df_features['is_weekend'] = (df_features['publish_day_of_week'] >= 5).astype(int)
    df_features['is_business_hours'] = (
        (df_features['publish_hour'] >= 9) & (df_features['publish_hour'] <= 17)
    ).astype(int)
    df_features['is_prime_time'] = (
        (df_features['publish_hour'] >= 19) & (df_features['publish_hour'] <= 22)
    ).astype(int)
    
    # Days since reference date
    reference_date = df_features['publish_date'].min()
    df_features['days_since_start'] = (df_features['publish_date'] - reference_date).dt.days
    
    print(f"✅ Created {len([col for col in df_features.columns if col not in df.columns])} temporal features")
    return df_features


@task
def create_engagement_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features related to user engagement"""
    print("👥 Creating engagement features...")
    
    df_features = df.copy()
    
    # Engagement ratios
    df_features['like_to_view_ratio'] = (
        df_features['like_count'] / (df_features['view_count'] + 1)
    )
    df_features['comment_to_view_ratio'] = (
        df_features['comment_count'] / (df_features['view_count'] + 1)
    )
    df_features['comment_to_like_ratio'] = (
        df_features['comment_count'] / (df_features['like_count'] + 1)
    )
    
    # Engagement score (composite metric)
    df_features['engagement_score'] = (
        df_features['like_count'] * 1.0 +
        df_features['comment_count'] * 2.0 +
        df_features['view_count'] * 0.1
    )
    
    # Engagement per word (content efficiency)
    df_features['engagement_per_word'] = (
        df_features['engagement_score'] / (df_features['body_word_count'] + 1)
    )
    
    # Virality indicators
    df_features['is_viral'] = (
        df_features['engagement_score'] > df_features['engagement_score'].quantile(0.95)
    ).astype(int)
    
    # Reading efficiency
    df_features['views_per_minute'] = (
        df_features['view_count'] / (df_features['reading_time_minutes'] + 1)
    )
    
    print(f"✅ Created {len([col for col in df_features.columns if col not in df.columns])} engagement features")
    return df_features


@task
def create_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features from categorical variables"""
    print("🏷️ Creating categorical features...")
    
    df_features = df.copy()
    
    # Author-based features
    author_stats = df_features.groupby('author_id').agg({
        'view_count': ['mean', 'std', 'count'],
        'like_count': 'mean',
        'comment_count': 'mean',
        'engagement_score': 'mean'
    }).round(2)
    
    # Flatten column names
    author_stats.columns = ['_'.join(col).strip() for col in author_stats.columns]
    author_stats = author_stats.add_prefix('author_')
    
    # Merge author stats back to main dataframe
    df_features = df_features.merge(
        author_stats, 
        left_on='author_id', 
        right_index=True, 
        how='left'
    )
    
    # Category-based features
    category_stats = df_features.groupby('category').agg({
        'view_count': 'mean',
        'engagement_score': 'mean',
        'reading_time_minutes': 'mean'
    }).round(2)
    
    category_stats.columns = [f'category_{col}' for col in category_stats.columns]
    df_features = df_features.merge(
        category_stats,
        left_on='category',
        right_index=True,
        how='left'
    )
    
    # One-hot encoding for category (if needed for some models)
    category_dummies = pd.get_dummies(df_features['category'], prefix='category')
    df_features = pd.concat([df_features, category_dummies], axis=1)
    
    # Author productivity features
    df_features['author_is_prolific'] = (
        df_features['author_view_count_count'] > df_features['author_view_count_count'].quantile(0.8)
    ).astype(int)
    
    print(f"✅ Created {len([col for col in df_features.columns if col not in df.columns])} categorical features")
    return df_features


@task
def create_tfidf_features(df: pd.DataFrame, max_features: int = 100) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create TF-IDF features from text content"""
    print(f"🔤 Creating TF-IDF features (max_features={max_features})...")
    
    # Combine title and body for TF-IDF
    df['combined_text'] = df['title'] + ' ' + df['body']
    
    # Initialize TF-IDF vectorizer
    tfidf = TfidfVectorizer(
        max_features=max_features,
        stop_words='english',
        ngram_range=(1, 2),  # Include bigrams
        min_df=2,  # Ignore terms that appear in less than 2 documents
        max_df=0.8  # Ignore terms that appear in more than 80% of documents
    )
    
    # Fit and transform
    tfidf_matrix = tfidf.fit_transform(df['combined_text'])
    
    # Create DataFrame with TF-IDF features
    feature_names = [f'tfidf_{name}' for name in tfidf.get_feature_names_out()]
    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=feature_names,
        index=df.index
    )
    
    # Combine with original features
    df_with_tfidf = pd.concat([df, tfidf_df], axis=1)
    
    # Store TF-IDF metadata for later use
    tfidf_metadata = {
        'feature_names': feature_names,
        'vocabulary_size': len(tfidf.vocabulary_),
        'max_features': max_features,
        'ngram_range': tfidf.ngram_range
    }
    
    print(f"✅ Created {len(feature_names)} TF-IDF features")
    return df_with_tfidf, tfidf_metadata


@task
def scale_numerical_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Scale numerical features for ML models"""
    print("📏 Scaling numerical features...")
    
    # Identify numerical columns (excluding ID and categorical)
    exclude_cols = ['id', 'title', 'body', 'category', 'author_id', 'publish_date', 'combined_text']
    categorical_cols = [col for col in df.columns if col.startswith('category_') and col != 'category']
    
    numerical_cols = [
        col for col in df.columns 
        if col not in exclude_cols + categorical_cols
        and df[col].dtype in ['int64', 'float64']
        and not col.startswith('tfidf_')  # Don't scale TF-IDF features
    ]
    
    df_scaled = df.copy()
    
    # Initialize scaler
    scaler = StandardScaler()
    
    # Scale numerical features
    if numerical_cols:
        df_scaled[numerical_cols] = scaler.fit_transform(df[numerical_cols])
        
        scaling_metadata = {
            'scaled_columns': numerical_cols,
            'scaler_mean': scaler.mean_.tolist(),
            'scaler_scale': scaler.scale_.tolist()
        }
        
        print(f"✅ Scaled {len(numerical_cols)} numerical features")
    else:
        scaling_metadata = {'scaled_columns': []}
        print("⚠️ No numerical features found to scale")
    
    return df_scaled, scaling_metadata


@task
def save_feature_metadata(
    tfidf_metadata: Dict[str, Any],
    scaling_metadata: Dict[str, Any],
    feature_columns: List[str],
    output_dir: str = "/tmp/datalake"
) -> str:
    """Save feature engineering metadata for reproducibility"""
    print("💾 Saving feature engineering metadata...")
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    metadata = {
        'feature_engineering_timestamp': datetime.now().isoformat(),
        'total_features': len(feature_columns),
        'feature_columns': feature_columns,
        'tfidf_metadata': tfidf_metadata,
        'scaling_metadata': scaling_metadata,
        'feature_types': {
            'text_features': [col for col in feature_columns if any(x in col for x in ['title_', 'body_', 'readability'])],
            'temporal_features': [col for col in feature_columns if any(x in col for x in ['hour', 'day', 'month', 'weekend', 'business'])],
            'engagement_features': [col for col in feature_columns if any(x in col for x in ['ratio', 'engagement', 'viral'])],
            'categorical_features': [col for col in feature_columns if col.startswith('category_')],
            'author_features': [col for col in feature_columns if col.startswith('author_')],
            'tfidf_features': [col for col in feature_columns if col.startswith('tfidf_')]
        }
    }
    
    # Save metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata_path = f"{output_dir}/feature_metadata_{timestamp}.json"
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Feature metadata saved to: {metadata_path}")
    return metadata_path


@flow(name="Feature Engineering Pipeline", description="Comprehensive feature engineering for ML")
def feature_engineering_pipeline(
    data_source: str = "/tmp/datalake",
    output_dir: str = "/tmp/datalake",
    max_tfidf_features: int = 100
):
    """
    Feature Engineering Pipeline for Machine Learning:
    1. Load raw data
    2. Create text features
    3. Create temporal features
    4. Create engagement features
    5. Create categorical features
    6. Create TF-IDF features
    7. Scale numerical features
    8. Save processed features and metadata
    """
    print("🚀 Starting Feature Engineering Pipeline...")
    
    # Load raw data
    raw_data = load_raw_data(data_source)
    
    # Create different types of features
    data_with_text = create_text_features(raw_data)
    data_with_temporal = create_temporal_features(data_with_text)
    data_with_engagement = create_engagement_features(data_with_temporal)
    data_with_categorical = create_categorical_features(data_with_engagement)
    
    # Create TF-IDF features
    data_with_tfidf, tfidf_metadata = create_tfidf_features(
        data_with_categorical, max_tfidf_features
    )
    
    # Scale numerical features
    final_features, scaling_metadata = scale_numerical_features(data_with_tfidf)
    
    # Save feature metadata
    metadata_path = save_feature_metadata(
        tfidf_metadata, scaling_metadata, list(final_features.columns), output_dir
    )
    
    # Save processed features
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    features_path = f"{output_dir}/ml_features_{timestamp}.parquet"
    final_features.to_parquet(features_path, index=False)
    
    print("🎉 Feature Engineering Pipeline completed!")
    
    return {
        'pipeline_status': 'completed',
        'total_features': len(final_features.columns),
        'total_records': len(final_features),
        'features_file': features_path,
        'metadata_file': metadata_path,
        'feature_summary': {
            'text_features': len([col for col in final_features.columns if any(x in col for x in ['title_', 'body_', 'readability'])]),
            'temporal_features': len([col for col in final_features.columns if any(x in col for x in ['hour', 'day', 'month', 'weekend', 'business'])]),
            'engagement_features': len([col for col in final_features.columns if any(x in col for x in ['ratio', 'engagement', 'viral'])]),
            'categorical_features': len([col for col in final_features.columns if col.startswith('category_')]),
            'author_features': len([col for col in final_features.columns if col.startswith('author_')]),
            'tfidf_features': len([col for col in final_features.columns if col.startswith('tfidf_')])
        },
        'execution_time': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the flow locally for testing
    print("🧪 Running Feature Engineering Pipeline locally...")
    result = feature_engineering_pipeline()
    print(f"🎯 Pipeline result: {result['pipeline_status']}")
    print(f"📊 Total features created: {result['total_features']}")
    print(f"📄 Features file: {result['features_file']}")
    print(f"📋 Metadata file: {result['metadata_file']}")

