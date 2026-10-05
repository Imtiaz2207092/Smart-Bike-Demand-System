"""
Demand Forecasting Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import os
import joblib
import pandas as pd
import numpy as np
from ml_engine.src.feature_engineering import extract_features, get_feature_columns

class DemandForecaster:
    """Inference Engine for Bike Demand Forecasting."""
    
    def __init__(self, model_path: str = "ml_engine/models_saved/xgboost.joblib"):
        self.model_path = model_path
        self.model = self._load_model()
        self.feature_columns = get_feature_columns()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}.")
        return joblib.load(self.model_path)

    def predict_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df_feat = extract_features(df)
        X = df_feat[self.feature_columns]
        
        preds = self.model.predict(X)
        preds = np.clip(preds, a_min=0, a_max=None)
        
        result_df = df.copy()
        result_df['predicted_demand'] = np.round(preds).astype(int)
        result_df['is_peak_hour'] = df_feat['is_peak_hour']
        return result_df

    def predict_single(self, input_dict: dict) -> dict:
        df = pd.DataFrame([input_dict])
        if 'datetime' not in df.columns:
            df['datetime'] = pd.to_datetime('now')
        else:
            df['datetime'] = pd.to_datetime(df['datetime'])
            
        res_df = self.predict_df(df)
        return {
            "predicted_demand": int(res_df['predicted_demand'].iloc[0]),
            "is_peak_hour": int(res_df['is_peak_hour'].iloc[0])
        }
