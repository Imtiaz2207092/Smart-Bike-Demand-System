"""
Main Pipeline Execution Script (50% Milestone Execution)
Author: Imtiaj Ahmad (Roll: 2207092)

Phase 1 (First 50% Sequence):
1. Data Ingestion & Cleaning (data_cleaning.py)
2. Feature Engineering (feature_engineering.py)
3. Model Development & Training (models.py)
"""

import os
import sys

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml_engine.src.data_cleaning import load_and_clean_data
from ml_engine.src.feature_engineering import extract_features, get_feature_columns
from ml_engine.src.models import BikeDemandModelTrainer

def run_ml_pipeline():
    print("=" * 60)
    print("      SMART BIKE DEMAND SYSTEM - ML ENGINE (50% MILESTONE)      ")
    print("            Developer: Imtiaj Ahmad (Roll: 2207092)             ")
    print("=" * 60)

    train_path = "ml_engine/data/train.csv"

    # Step 1: Data Collection & Cleaning
    print("\n[Step 1/3] Loading & Cleaning Dataset...")
    df_train_raw = load_and_clean_data(train_path, is_train=True)
    print(f"[OK] Data cleaned successfully: {df_train_raw.shape[0]} rows, {df_train_raw.shape[1]} columns.")

    # Step 2: Feature Engineering
    print("\n[Step 2/3] Performing Feature Engineering...")
    df_train_feat = extract_features(df_train_raw)
    feature_cols = get_feature_columns()
    target_col = 'count' if 'count' in df_train_feat.columns else 'total_demand'
    print(f"[OK] Extracted {len(feature_cols)} features: {feature_cols}")

    # Train / Validation Split
    split_idx = int(len(df_train_feat) * 0.8)
    train_data = df_train_feat.iloc[:split_idx]
    val_data = df_train_feat.iloc[split_idx:]

    X_train, y_train = train_data[feature_cols], train_data[target_col]
    X_val, y_val = val_data[feature_cols], val_data[target_col]

    # Step 3: Model Development & Training
    print("\n[Step 3/3] Training Machine Learning Models...")
    trainer = BikeDemandModelTrainer()
    
    print("  - Training Baseline (Linear Regression)...")
    trainer.train_linear_regression(X_train, y_train)
    
    print("  - Training Ensemble (Random Forest Regressor)...")
    trainer.train_random_forest(X_train, y_train, n_estimators=100, max_depth=12)
    
    print("  - Training Gradient Boosting (XGBoost Regressor)...")
    trainer.train_xgboost(X_train, y_train, n_estimators=150, learning_rate=0.08, max_depth=6)

    # Save models
    for model_name in trainer.trained_models:
        saved_path = trainer.save_model(model_name)
        print(f"[OK] Saved {model_name} model to {saved_path}")

    print("\n" + "=" * 60)
    print("  SUCCESS: 50% MILESTONE OF ML PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_ml_pipeline()
