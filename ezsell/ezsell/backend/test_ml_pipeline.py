"""
Quick Test Script for ML Pipeline
Tests scraping and preprocessing with small sample
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from scrapers import MobileScraper
from ml_pipeline import DataPreprocessor
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mobile_scraping():
    """Test mobile scraping with 1 page"""
    logger.info("=" * 80)
    logger.info("TESTING MOBILE SCRAPER")
    logger.info("=" * 80)
    
    try:
        scraper = MobileScraper()
        data = scraper.scrape(max_pages=1, max_listings=10)
        
        if data:
            df = pd.DataFrame(data)
            logger.info(f"\n✅ Successfully scraped {len(df)} mobile listings")
            logger.info(f"\nSample data:")
            logger.info(df[['title', 'brand', 'price', 'ram', 'storage']].head())
            
            # Save test data
            df.to_csv('test_mobile_data.csv', index=False)
            logger.info(f"\n✅ Saved to test_mobile_data.csv")
            
            return df
        else:
            logger.error("❌ No data scraped")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_preprocessing(df):
    """Test preprocessing"""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING PREPROCESSOR")
    logger.info("=" * 80)
    
    try:
        preprocessor = DataPreprocessor()
        df_processed = preprocessor.preprocess_mobile_data(df)
        
        if df_processed is not None and len(df_processed) > 0:
            logger.info(f"\n✅ Successfully preprocessed {len(df_processed)} records")
            logger.info(f"\nProcessed features:")
            logger.info(df_processed.columns.tolist())
            
            # Save processed data
            df_processed.to_csv('test_mobile_processed.csv', index=False)
            logger.info(f"\n✅ Saved to test_mobile_processed.csv")
            
            return df_processed
        else:
            logger.error("❌ Preprocessing failed")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run quick test"""
    logger.info("\n" + "#" * 80)
    logger.info("# ML PIPELINE QUICK TEST")
    logger.info("#" * 80 + "\n")
    
    # Test scraping
    df = test_mobile_scraping()
    
    if df is not None and len(df) > 0:
        # Test preprocessing
        df_processed = test_preprocessing(df)
        
        if df_processed is not None:
            logger.info("\n" + "=" * 80)
            logger.info("✅ ALL TESTS PASSED!")
            logger.info("=" * 80)
            logger.info("\nYou can now run the full pipeline:")
            logger.info("  python run_ml_pipeline.py --category mobile --max-pages 5")
            logger.info("=" * 80 + "\n")
        else:
            logger.error("\n❌ Preprocessing test failed")
    else:
        logger.error("\n❌ Scraping test failed")
        logger.info("\nNote: If scraping failed, it might be due to:")
        logger.info("  1. Internet connection issues")
        logger.info("  2. OLX website structure changes")
        logger.info("  3. Rate limiting")
        logger.info("\nYou can still use existing CSV files with:")
        logger.info("  python run_ml_pipeline.py --skip-scraping --csv-file your_data.csv")


if __name__ == '__main__':
    main()
