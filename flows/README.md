# Data Lake Flows

This directory contains the data collection and processing pipelines for our Data Lake.

## 🌡️ Weather Data Collection

### Campinas Temperature Pipeline
- **File:** `weather/campinas_temperature.py`
- **Purpose:** Collects current temperature and weather data for Campinas, SP, Brazil
- **Schedule:** Runs automatically every 30 minutes
- **Output:** 
  - Latest reading: `/app/data/campinas_temperature_latest.json`
  - Historical data: `/app/data/campinas_temperature_history.csv`

### Pipeline Features
- **Real weather data** from wttr.in API
- **Data validation** and quality scoring
- **Error handling** with fallback mock data
- **Historical tracking** in CSV format
- **Summary statistics** generation

## 🎯 Data Lake Focus

This Data Lake is designed to:
1. **Collect data** from various sources
2. **Store raw data** in organized structure
3. **Provide foundation** for future analytics

### Current Data Sources
- ✅ **Weather data** (Campinas temperature)
- 🔄 **More sources coming soon...**

## 🔧 Development

### Running Locally
```python
# Test individual pipeline
cd flows/weather/
python campinas_temperature.py
```

### Adding New Data Sources
1. Create new directory under `flows/` (e.g., `flows/finance/`)
2. Add pipeline following the same pattern
3. Focus on data collection and basic validation
4. Store in simple formats (JSON, CSV)

## 📊 Data Access

All collected data is stored in `/app/data/` directory:
- **JSON files** for latest readings
- **CSV files** for historical data
- **Simple structure** for easy access

The goal is to build a solid foundation for data collection before moving to complex analytics.

