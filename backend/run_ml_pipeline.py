"""
Main Pipeline Script - Complete ML Pipeline Orchestrator
Scrapes data from OLX, preprocesses, trains models, and evaluates
Run this script to execute the complete pipeline

Usage:
    python run_ml_pipeline.py --category all --max-pages 10 --max-listings 500
    python run_ml_pipeline.py --category mobile --max-pages 5
"""

import argparse
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from scrapers import MobileScraper, LaptopScraper, FurnitureScraper
from ml_pipeline import DataPreprocessor, PricePredictionTrainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MLPipeline:
    """Complete ML Pipeline for Price Prediction"""
    
    def __init__(self, data_dir: str = "scraped_data", model_dir: str = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.model_dir.mkdir(exist_ok=True)
        
        self.preprocessor = DataPreprocessor()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def scrape_data(self, category: str, max_pages: int = 10, max_listings: int = 500) -> pd.DataFrame:
        """Scrape data for a specific category"""
        logger.info(f"{'='*80}")
        logger.info(f"SCRAPING {category.upper()} DATA FROM OLX PAKISTAN")
        logger.info(f"{'='*80}")
        
        # Initialize scraper
        if category == 'mobile':
            scraper = MobileScraper()
        elif category == 'laptop':
            scraper = LaptopScraper()
        elif category == 'furniture':
            scraper = FurnitureScraper()
        else:
            raise ValueError(f"Unknown category: {category}")
        
        # Scrape
        try:
            data = scraper.scrape(max_pages=max_pages, max_listings=max_listings)
            
            if not data:
                logger.warning(f"No data scraped for {category}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Save raw data
            raw_file = self.data_dir / f"{category}_raw_{self.timestamp}.csv"
            df.to_csv(raw_file, index=False)
            logger.info(f"Raw data saved to {raw_file}")
            logger.info(f"Scraped {len(df)} {category} listings")
            
            return df
            
        except Exception as e:
            logger.error(f"Error scraping {category} data: {e}")
            return None
    
    def preprocess_data(self, df: pd.DataFrame, category: str) -> pd.DataFrame:
        """Preprocess scraped data"""
        logger.info(f"{'='*80}")
        logger.info(f"PREPROCESSING {category.upper()} DATA")
        logger.info(f"{'='*80}")
        
        try:
            if category == 'mobile':
                df_processed = self.preprocessor.preprocess_mobile_data(df)
            elif category == 'laptop':
                df_processed = self.preprocessor.preprocess_laptop_data(df)
            elif category == 'furniture':
                df_processed = self.preprocessor.preprocess_furniture_data(df)
            else:
                raise ValueError(f"Unknown category: {category}")
            
            # Save preprocessed data
            processed_file = self.data_dir / f"{category}_preprocessed_{self.timestamp}.csv"
            df_processed.to_csv(processed_file, index=False)
            logger.info(f"Preprocessed data saved to {processed_file}")
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error preprocessing {category} data: {e}")
            return None
    
    def train_model(self, df: pd.DataFrame, category: str) -> dict:
        """Train price prediction model"""
        logger.info(f"{'='*80}")
        logger.info(f"TRAINING {category.upper()} PRICE PREDICTION MODEL")
        logger.info(f"{'='*80}")
        
        try:
            # Prepare features
            X, feature_names = self.preprocessor.prepare_features(df, category)
            y = df['price']
            
            logger.info(f"Feature set: {len(feature_names)} features")
            logger.info(f"Features: {feature_names}")
            
            # Initialize trainer
            trainer = PricePredictionTrainer(category=category, output_dir=str(self.model_dir))
            
            # Train
            metrics = trainer.train_pipeline(X, y, feature_names, test_size=0.2)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training {category} model: {e}")
            return None
    
    def run_category(self, category: str, max_pages: int = 10, max_listings: int = 500, 
                    skip_scraping: bool = False, csv_file: str = None):
        """Run complete pipeline for a category"""
        logger.info(f"\n{'#'*80}")
        logger.info(f"# STARTING PIPELINE FOR {category.upper()}")
        logger.info(f"{'#'*80}\n")
        
        try:
            # Step 1: Scrape or load data
            if skip_scraping and csv_file:
                logger.info(f"Loading data from {csv_file}")
                df = pd.read_csv(csv_file)
            else:
                df = self.scrape_data(category, max_pages, max_listings)
            
            if df is None or len(df) == 0:
                logger.error(f"No data available for {category}")
                return None
            
            # Step 2: Preprocess
            df_processed = self.preprocess_data(df, category)
            
            if df_processed is None or len(df_processed) == 0:
                logger.error(f"Preprocessing failed for {category}")
                return None
            
            # Step 3: Train model
            metrics = self.train_model(df_processed, category)
            
            if metrics:
                logger.info(f"\n{'='*80}")
                logger.info(f"PIPELINE COMPLETE FOR {category.upper()}")
                logger.info(f"{'='*80}")
                logger.info(f"Final Model Accuracy: {metrics['accuracy_percent']:.2f}%")
                logger.info(f"Test R² Score: {metrics['test_r2']:.4f}")
                logger.info(f"Mean Absolute Error: Rs. {metrics['mae']:.2f}")
                logger.info(f"Mean Absolute Percentage Error: {metrics['mape']:.2f}%")
                logger.info(f"{'='*80}\n")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Pipeline error for {category}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_all_categories(self, max_pages: int = 10, max_listings: int = 500):
        """Run pipeline for all categories"""
        logger.info(f"\n{'#'*80}")
        logger.info(f"# RUNNING COMPLETE ML PIPELINE FOR ALL CATEGORIES")
        logger.info(f"# Timestamp: {self.timestamp}")
        logger.info(f"{'#'*80}\n")
        
        categories = ['mobile', 'laptop', 'furniture']
        results = {}
        
        for category in categories:
            metrics = self.run_category(category, max_pages, max_listings)
            results[category] = metrics
        
        # Summary
        logger.info(f"\n{'#'*80}")
        logger.info(f"# PIPELINE SUMMARY")
        logger.info(f"{'#'*80}\n")
        
        for category, metrics in results.items():
            if metrics:
                logger.info(f"{category.upper()}:")
                logger.info(f"  Accuracy: {metrics['accuracy_percent']:.2f}%")
                logger.info(f"  R² Score: {metrics['test_r2']:.4f}")
                logger.info(f"  MAE: Rs. {metrics['mae']:.2f}")
                logger.info(f"  MAPE: {metrics['mape']:.2f}%")
            else:
                logger.info(f"{category.upper()}: FAILED")
            logger.info("")
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='OLX Pakistan Price Prediction ML Pipeline')
    
    parser.add_argument('--category', type=str, default='all',
                       choices=['all', 'mobile', 'laptop', 'furniture'],
                       help='Category to process (default: all)')
    
    parser.add_argument('--max-pages', type=int, default=10,
                       help='Maximum pages to scrape per category (default: 10)')
    
    parser.add_argument('--max-listings', type=int, default=500,
                       help='Maximum listings to scrape per category (default: 500)')
    
    parser.add_argument('--data-dir', type=str, default='scraped_data',
                       help='Directory to save scraped data (default: scraped_data)')
    
    parser.add_argument('--model-dir', type=str, default=None,
                       help='Directory to save trained models (default: current directory)')
    
    parser.add_argument('--skip-scraping', action='store_true',
                       help='Skip scraping and use existing CSV file')
    
    parser.add_argument('--csv-file', type=str, default=None,
                       help='CSV file to use if skipping scraping')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = MLPipeline(data_dir=args.data_dir, model_dir=args.model_dir)
    
    # Run pipeline
    if args.category == 'all':
        results = pipeline.run_all_categories(
            max_pages=args.max_pages,
            max_listings=args.max_listings
        )
    else:
        results = pipeline.run_category(
            category=args.category,
            max_pages=args.max_pages,
            max_listings=args.max_listings,
            skip_scraping=args.skip_scraping,
            csv_file=args.csv_file
        )
    
    logger.info("\n" + "="*80)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("="*80)


if __name__ == '__main__':
    main()
