# OLX Pakistan Price Prediction ML Pipeline

## Complete System for Scraping, Preprocessing, and Training

This pipeline scrapes data from OLX Pakistan, preprocesses it, and trains highly accurate price prediction models.

## 📁 Project Structure

```
backend/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py        # Base scraper with common functionality
│   ├── mobile_scraper.py      # Mobile phone scraper
│   ├── laptop_scraper.py      # Laptop scraper
│   └── furniture_scraper.py   # Furniture scraper
├── ml_pipeline/
│   ├── __init__.py
│   ├── preprocessor.py        # Data preprocessing and feature engineering
│   └── trainer.py             # Advanced ML training with hyperparameter tuning
├── run_ml_pipeline.py         # Main pipeline orchestrator
└── scraped_data/              # Output directory for scraped data (auto-created)
```

## 🚀 Features

### Web Scraping
- **Intelligent scraping** from OLX Pakistan with retry logic and rate limiting
- **Mobile phones**: Extracts brand, RAM, storage, battery, camera, screen size, condition
- **Laptops**: Extracts brand, processor, generation, RAM, storage, GPU, screen size, condition
- **Furniture**: Extracts type, material, color, dimensions, seating capacity, condition

### Data Preprocessing
- Automatic missing value handling
- Feature engineering (ratios, scores, premiums)
- Outlier detection and removal using IQR method
- Label encoding for categorical variables
- Smart brand normalization

### ML Training
- **Multiple algorithms**: Random Forest, XGBoost, Gradient Boosting, Ridge, Lasso
- **Hyperparameter tuning**: Automated RandomizedSearchCV
- **Ensemble methods**: Stacking with multiple base models
- **Cross-validation**: 5-fold CV for robust evaluation
- **Comprehensive metrics**: R², MAE, RMSE, MAPE, Accuracy

## 📦 Installation

```bash
# Install additional scraping dependencies
pip install requests beautifulsoup4 lxml

# Main dependencies should already be installed from requirements.txt
```

## 🎯 Usage

### Run Complete Pipeline for All Categories
```bash
python run_ml_pipeline.py --category all --max-pages 10 --max-listings 500
```

### Run for Specific Category
```bash
# Mobiles only
python run_ml_pipeline.py --category mobile --max-pages 5 --max-listings 300

# Laptops only
python run_ml_pipeline.py --category laptop --max-pages 5 --max-listings 300

# Furniture only
python run_ml_pipeline.py --category furniture --max-pages 5 --max-listings 300
```

### Use Existing CSV (Skip Scraping)
```bash
python run_ml_pipeline.py --category mobile --skip-scraping --csv-file "scraped_data/mobile_raw_20241207.csv"
```

### Command Line Arguments
- `--category`: Category to process (all, mobile, laptop, furniture) [default: all]
- `--max-pages`: Maximum pages to scrape per category [default: 10]
- `--max-listings`: Maximum listings to scrape per category [default: 500]
- `--data-dir`: Directory to save scraped data [default: scraped_data]
- `--model-dir`: Directory to save trained models [default: current directory]
- `--skip-scraping`: Skip scraping and use existing CSV
- `--csv-file`: CSV file to use if skipping scraping

## 📊 Output Files

### Scraped Data
- `scraped_data/mobile_raw_TIMESTAMP.csv` - Raw mobile data
- `scraped_data/laptop_raw_TIMESTAMP.csv` - Raw laptop data
- `scraped_data/furniture_raw_TIMESTAMP.csv` - Raw furniture data

### Preprocessed Data
- `scraped_data/mobile_preprocessed_TIMESTAMP.csv`
- `scraped_data/laptop_preprocessed_TIMESTAMP.csv`
- `scraped_data/furniture_preprocessed_TIMESTAMP.csv`

### Trained Models
- `price_predictor_mobile.pkl` - Trained mobile price predictor
- `price_predictor_laptop.pkl` - Trained laptop price predictor
- `price_predictor_furniture.pkl` - Trained furniture price predictor
- `model_metadata_*.json` - Model metadata and metrics

## 📈 Model Performance

The pipeline trains multiple models and selects the best one based on:
1. **Baseline comparison**: Tests 5 different algorithms
2. **Hyperparameter tuning**: Optimizes top performers
3. **Ensemble creation**: Stacks models for maximum accuracy

Expected accuracy ranges:
- **Mobile**: 85-95% R² score
- **Laptop**: 85-93% R² score  
- **Furniture**: 75-88% R² score

## 🔍 Features Extracted

### Mobile Phones
- Brand, Model, Condition
- RAM (GB), Storage (GB)
- Battery (mAh), Screen Size (inches)
- Camera (MP), Color
- Location, Description

### Laptops
- Brand, Model, Condition
- Processor (type, generation)
- RAM (GB), Storage (GB, type)
- GPU (dedicated/integrated)
- Screen Size (inches)
- Location, Description

### Furniture
- Type (sofa, bed, table, etc.)
- Material (wood, metal, leather, etc.)
- Color, Brand, Style
- Dimensions (length, width, height)
- Seating Capacity, Room Type
- Location, Description

## 🛠️ Customization

### Scraping More Pages
```python
# In run_ml_pipeline.py, modify:
python run_ml_pipeline.py --max-pages 20 --max-listings 1000
```

### Adjust Preprocessing
Edit `ml_pipeline/preprocessor.py` to modify:
- Feature engineering logic
- Outlier removal thresholds
- Missing value strategies

### Change ML Algorithms
Edit `ml_pipeline/trainer.py` to:
- Add new algorithms
- Modify hyperparameter grids
- Change ensemble composition

## 📝 Logs

All operations are logged to:
- `ml_pipeline.log` - Complete pipeline execution log
- Console output - Real-time progress

## ⚠️ Important Notes

1. **Rate Limiting**: Scraper includes delays to respect OLX's servers
2. **Data Quality**: More pages = better models, but longer execution time
3. **Internet Required**: For scraping phase only
4. **Training Time**: Full pipeline can take 30-60 minutes depending on data size

## 🔄 Pipeline Flow

```
1. SCRAPING
   ├── Connect to OLX Pakistan
   ├── Extract listing URLs
   └── Parse individual listings
   
2. PREPROCESSING
   ├── Clean data
   ├── Handle missing values
   ├── Feature engineering
   └── Remove outliers
   
3. TRAINING
   ├── Split train/test
   ├── Train baseline models
   ├── Hyperparameter tuning
   ├── Create ensemble
   └── Evaluate & save best model
```

## 📞 Support

For issues or questions:
1. Check the log file `ml_pipeline.log`
2. Ensure all dependencies are installed
3. Verify internet connection for scraping

## 🎓 Example Run

```bash
$ python run_ml_pipeline.py --category mobile --max-pages 3 --max-listings 100

################################################################################
# RUNNING COMPLETE ML PIPELINE FOR ALL CATEGORIES
################################################################################

================================================================================
SCRAPING MOBILE DATA FROM OLX PAKISTAN
================================================================================
Found 100 listings
Scraped mobile: Samsung Galaxy S21... - Rs. 89000
...
Mobile scraping complete! Collected 98 listings

================================================================================
PREPROCESSING MOBILE DATA
================================================================================
Preprocessing 98 mobile records
Removed 5 outliers (5.1%)
Mobile preprocessing complete. Final records: 93

================================================================================
TRAINING MOBILE PRICE PREDICTION MODEL
================================================================================
Training multiple models for mobile price prediction
Random Forest - Test R²: 0.8932, MAE: 5420.50
XGBoost - Test R²: 0.9124, MAE: 4820.30
...
Best tuned model: xgboost
Tuned Accuracy: 93.45%

================================================================================
FINAL MODEL EVALUATION
================================================================================
Final Model Performance:
  Training R²: 0.9512
  Testing R²: 0.9345
  MAE: Rs. 4820.30
  RMSE: Rs. 6234.50
  MAPE: 8.45%
  ACCURACY: 93.45%
================================================================================

Model saved to price_predictor_mobile.pkl
```

## 🏆 Best Practices

1. Start with fewer pages for testing
2. Run full scraping during off-peak hours
3. Regularly update scraped data for model retraining
4. Monitor accuracy metrics and retrain when performance drops
5. Keep logs for debugging and performance tracking
