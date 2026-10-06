"""
Unit Tests for Imtiaj Ahmad's ML Engine
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import os
import pytest
import pandas as pd
import numpy as np
from ml_engine.src.data_cleaning import load_and_clean_data
from ml_engine.src.feature_engineering import extract_features
from ml_engine.src.evaluation import calculate_metrics

def test_data_cleaning():
    train_path = "ml_engine/data/train.csv"
    if os.path.exists(train_path):
        df = load_and_clean_data(train_path, is_train=True)
        assert not df.empty
        assert 'datetime' in df.columns

def test_feature_engineering():
    dummy_data = pd.DataFrame({
        'datetime': pd.to_datetime(['2024-01-01 08:00:00', '2024-01-01 14:00:00']),
        'season': [1, 1],
        'holiday': [0, 0],
        'workingday': [1, 1],
        'weather': [1, 1],
        'temp': [15.0, 20.0],
        'atemp': [14.0, 19.0],
        'humidity': [60, 50],
        'windspeed': [10.0, 5.0]
    })
    
    df_feat = extract_features(dummy_data)
    assert 'is_peak_hour' in df_feat.columns
    assert df_feat['is_peak_hour'].iloc[0] == 1

def test_metrics_calculation():
    y_true = np.array([10, 20, 30, 40, 50])
    y_pred = np.array([12, 18, 32, 38, 52])
    metrics = calculate_metrics(y_true, y_pred)
    assert metrics['MAE'] == 2.0
