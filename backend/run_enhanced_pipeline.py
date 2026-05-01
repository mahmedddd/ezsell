"""
Enhanced ML Pipeline Runner with Advanced Feature Extraction
Targets 70%+ accuracy using NLP, regex, and sophisticated preprocessing
"""

import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
from ml_pipeline.enhanced_preprocessor import EnhancedPreprocessor
from ml_pipeline.trainer import PricePredictionTrainer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.FileHandler('enhanced_ml_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMLPipeline:
    """Enhanced ML Pipeline with advanced feature extraction"""
    
    def __init__(self, category: str):
        self.category = category
        self.preprocessor = EnhancedPreprocessor()
        self.trainer = PricePredictionTrainer(category)
        self.output_dir = Path('models_enhanced')
        self.output_dir.mkdir(exist_ok=True)
    
    def run(self, csv_file: str):
        """Run enhanced pipeline"""
        logger.info(f"\n{'#'*80}")
        logger.info(f"# ENHANCED PIPELINE FOR {self.category.upper()}")
        logger.info(f"# Target: 70%+ Accuracy with Advanced Feature Extraction")
        logger.info(f"{'#'*80}\n")
        
        # Load data
        logger.info(f"Loading data from {csv_file}")
        df = pd.read_csv(csv_file)
        logger.info(f"Loaded {len(df)} records")
        
        # Preprocess
        logger.info(f"\n{'='*80}")
        logger.info(f"ENHANCED PREPROCESSING {self.category.upper()} DATA")
        logger.info(f"{'='*80}")
        
        if self.category == 'mobile':
            df = self.preprocessor.preprocess_mobile_data(df)
        elif self.category == 'laptop':
            df = self.preprocessor.preprocess_laptop_data(df)
        elif self.category == 'furniture':
            df = self.preprocessor.preprocess_furniture_data(df)
        
        # Save preprocessed data
        preprocessed_file = f"scraped_data/{self.category}_enhanced_preprocessed.csv"
        df.to_csv(preprocessed_file, index=False)
        logger.info(f"Preprocessed data saved to {preprocessed_file}")
        
        # Prepare features
        logger.info(f"\n{'='*80}")
        logger.info(f"TRAINING ENHANCED {self.category.upper()} MODEL")
        logger.info(f"{'='*80}")
        
        X, y, feature_names = self.preprocessor.prepare_features(df, self.category)
        
        logger.info(f"Feature set: {len(feature_names)} features")
        logger.info(f"Features: {feature_names}")
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Train enhanced model
        model, results = self.trainer.train_best_model(
            X_train, y_train, X_test, y_test,
            use_tuning=True, use_ensemble=True
        )
        
        # Store feature names
        results['feature_names'] = feature_names
        
        # Save model
        model_file = self.output_dir / f"price_predictor_{self.category}_enhanced.pkl"
        
        import joblib
        joblib.dump(model, str(model_file))
        logger.info(f"Model saved to {model_file}")
        
        # Save metadata
        metadata_file = self.output_dir / f"model_metadata_{self.category}_enhanced.json"
        import json
        metadata = {
            'category': self.category,
            'feature_names': feature_names,
            'metrics': {
                'train_r2': results.get('train_r2', 0),
                'test_r2': results.get('test_r2', 0),
                'mae': results.get('mae', 0),
                'rmse': results.get('rmse', 0),
                'mape': results.get('mape', 0),
                'accuracy_percent': results.get('accuracy_percent', results.get('test_accuracy', 0))
            },
            'num_features': len(feature_names),
            'training_samples': len(X_train)
        }
        with open(str(metadata_file), 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to {metadata_file}")
        
        # Display results
        accuracy = results.get('accuracy_percent', results.get('test_accuracy', 0))
        
        logger.info(f"\n{'='*80}")
        logger.info(f"ENHANCED PIPELINE COMPLETE FOR {self.category.upper()}")
        logger.info(f"{'='*80}")
        logger.info(f"Final Model Accuracy: {accuracy:.2f}%")
        logger.info(f"Test R² Score: {results['test_r2']:.4f}")
        logger.info(f"Mean Absolute Error: Rs. {results['mae']:,.2f}")
        logger.info(f"Mean Absolute Percentage Error: {results['mape']:.2f}%")
        logger.info(f"{'='*80}\n")
        
        # Check if target met
        if accuracy >= 70:
            logger.info("🎉 TARGET ACHIEVED: 70%+ accuracy!")
        else:
            logger.info(f"⚠️ Target not met. Current: {accuracy:.2f}%, Target: 70%")
            logger.info("Recommendations:")
            logger.info("  - Collect more data (current dataset may be too small)")
            logger.info("  - Add more category-specific features")
            logger.info("  - Use deep learning models (neural networks)")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Enhanced ML Pipeline with 80%+ target accuracy')
    parser.add_argument('--category', type=str, required=True,
                       choices=['mobile', 'laptop', 'furniture', 'all'],
                       help='Category to train')
    parser.add_argument('--csv-file', type=str,
                       help='CSV file to use (for single category)')
    
    args = parser.parse_args()
    
    if args.category == 'all':
        categories = ['mobile', 'laptop', 'furniture']
        csv_files = [
            'scraped_data/mobile_merged_all.csv',
            'scraped_data/laptop_merged_all.csv',
            'scraped_data/furniture_merged_all.csv'
        ]
        
        results_summary = {}
        
        for category, csv_file in zip(categories, csv_files):
            if Path(csv_file).exists():
                logger.info(f"\n🚀 Training {category.upper()} with {csv_file}")
                pipeline = EnhancedMLPipeline(category)
                results = pipeline.run(csv_file)
                results_summary[category] = results
            else:
                logger.error(f"CSV file not found: {csv_file}")
        
        # Overall summary
        logger.info(f"\n{'='*80}")
        logger.info("OVERALL ENHANCED TRAINING SUMMARY")
        logger.info(f"{'='*80}")
        
        if results_summary:
            for category, results in results_summary.items():
                accuracy = results.get('accuracy_percent', results.get('test_accuracy', 0))
                logger.info(f"\n{category.upper()}:")
                logger.info(f"  Accuracy: {accuracy:.2f}%")
                logger.info(f"  R²: {results['test_r2']:.4f}")
                logger.info(f"  MAE: Rs. {results['mae']:,.2f}")
            
            avg_accuracy = sum(r.get('accuracy_percent', r.get('test_accuracy', 0)) for r in results_summary.values()) / len(results_summary)
            logger.info(f"\nAverage Accuracy: {avg_accuracy:.2f}%")
            
            if avg_accuracy >= 80:
                logger.info("🎉 OVERALL TARGET ACHIEVED!")
        else:
            logger.error("No models were trained successfully!")
        
    else:
        if not args.csv_file:
            args.csv_file = f"scraped_data/{args.category}_merged_all.csv"
        
        if not Path(args.csv_file).exists():
            logger.error(f"CSV file not found: {args.csv_file}")
            return 1
        
        pipeline = EnhancedMLPipeline(args.category)
        pipeline.run(args.csv_file)
    
    logger.info(f"\n{'='*80}")
    logger.info("ENHANCED PIPELINE EXECUTION COMPLETE")
    logger.info(f"{'='*80}\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
