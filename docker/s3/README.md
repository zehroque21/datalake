# Local S3 Simulation Structure

This directory simulates an S3 bucket structure for local development and testing.

## 📁 Directory Structure

```
s3/
├── staging/    # Raw data as received from sources
├── raw/        # Cleaned and validated data
├── trusted/    # Processed and enriched data
└── refined/    # Analytics-ready data and aggregations
```

## 🎯 Data Lake Layers

### 📥 Staging
- **Purpose:** Temporary storage for incoming data
- **Format:** Original format from source
- **Retention:** Short-term (hours/days)
- **Example:** Raw API responses, uploaded files

### 🗃️ Raw
- **Purpose:** Permanent storage of source data
- **Format:** Standardized but unprocessed
- **Retention:** Long-term (years)
- **Example:** JSON, CSV, Parquet files with original data

### ✅ Trusted
- **Purpose:** Cleaned and validated data
- **Format:** Structured and consistent
- **Retention:** Long-term (years)
- **Example:** Validated records, deduplicated data

### 📊 Refined
- **Purpose:** Analytics-ready datasets
- **Format:** Optimized for queries
- **Retention:** Medium-term (months/years)
- **Example:** Aggregated tables, feature stores

## 🔧 Usage

The pipeline will automatically organize data into these layers:

1. **Ingest** → `staging/`
2. **Validate** → `raw/`
3. **Process** → `trusted/`
4. **Aggregate** → `refined/`

## 📝 Note

- All files in these directories are ignored by Git
- Only the directory structure is version controlled
- Data is ephemeral and recreated on each run

