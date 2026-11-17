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
from ml_engine.src.evaluation import calculate_metrics, evaluate_and_compare_models
from ml_engine.src.redistribution import detect_shortage_surplus, recommend_redistribution

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


def test_model_comparison_flattens_dnn_predictions(tmp_path):
    class DnnModel:
        coef_ = np.array([1.0])

        def predict(self, features):
            return np.array([[12.0], [18.0], [32.0]])

    features = pd.DataFrame({'feature': [1, 2, 3]})
    targets = pd.Series([10.0, 20.0, 30.0])

    comparison = evaluate_and_compare_models(
        {'DNN': DnnModel()},
        features,
        targets,
        reports_dir=str(tmp_path),
        training_history={
            'DNN': {'loss': [100.0, 40.0], 'val_loss': [120.0, 50.0]},
            'XGBoost': {'validation_0': {'rmse': [12.0, 8.0]}},
        },
    )

    assert comparison.loc[0, 'Model'] == 'DNN'
    assert comparison.loc[0, 'MAE'] == 2.0
    report = pd.read_json(tmp_path / 'model_comparison.json')
    assert report.loc[0, 'Model'] == 'DNN'
    assert (tmp_path / 'model_report.html').is_file()
    assert (tmp_path / 'figures' / 'model_metrics.png').is_file()
    assert (tmp_path / 'figures' / 'actual_vs_predicted.png').is_file()
    assert (tmp_path / 'figures' / 'residuals.png').is_file()
    assert (tmp_path / 'figures' / 'training_curves.png').is_file()
    assert (tmp_path / 'figures' / 'feature_importance_gain.png').is_file()
    html_report = (tmp_path / 'model_report.html').read_text(encoding='utf-8')
    assert 'data:image/png;base64,' in html_report
    assert 'Loss and validation learning curves' in html_report
    assert 'একই holdout data' in html_report


def test_shortage_surplus_and_recommendation():
    stations = pd.DataFrame([
        {'station_id': 'A', 'available_bikes': 5, 'predicted_demand': 18},
        {'station_id': 'B', 'available_bikes': 25, 'predicted_demand': 8},
        {'station_id': 'C', 'available_bikes': 12, 'predicted_demand': 7}
    ])

    shortage, surplus = detect_shortage_surplus(stations)
    assert 'A' in shortage['station_id'].values
    assert 'B' in surplus['station_id'].values

    recommendations = recommend_redistribution(stations)
    assert isinstance(recommendations, list)
    assert len(recommendations) >= 1
    assert recommendations[0]['from_station'] == 'B'
