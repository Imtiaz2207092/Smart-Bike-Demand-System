"""
Machine Learning Model Development Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

class BikeDemandModelTrainer:
    """
    Trains, tunes, saves, and loads ML models for bike demand prediction:
    1. Linear Regression (Baseline)
    2. Random Forest Regressor (Ensemble)
    3. XGBoost Regressor (State-of-the-Art Gradient Boosting)
    """
    
    def __init__(self, models_dir: str = "ml_engine/models_saved"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.trained_models = {}

    def train_linear_regression(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Trains baseline Linear Regression model."""
        model = LinearRegression()
        model.fit(X_train, y_train)
        self.trained_models['Linear Regression'] = model
        return model

    def train_random_forest(self, X_train: pd.DataFrame, y_train: pd.Series, n_estimators: int = 150, max_depth: int = 15):
        """Trains Random Forest Regressor model."""
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        self.trained_models['Random Forest'] = model
        return model

    def train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series, n_estimators: int = 200, learning_rate: float = 0.08, max_depth: int = 6):
        """Trains XGBoost Regressor model."""
        model = XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        self.trained_models['XGBoost'] = model
        return model

    def save_model(self, model_name: str, filename: str = None) -> str:
        """Saves trained model to disk using joblib."""
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} has not been trained yet.")
        
        if filename is None:
            filename = f"{model_name.lower().replace(' ', '_')}.joblib"
            
        filepath = os.path.join(self.models_dir, filename)
        joblib.dump(self.trained_models[model_name], filepath)
        return filepath

    @staticmethod
    def load_model(filepath: str):
        """Loads model from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Saved model file not found at {filepath}")
        return joblib.load(filepath)
