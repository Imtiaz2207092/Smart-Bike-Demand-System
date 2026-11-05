"""
Machine Learning Model Development Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import os
import joblib
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

class BikeDemandModelTrainer:
    """
    Trains, tunes, saves, and loads ML models for bike demand prediction:
    1. Linear Regression (Baseline)
    2. Random Forest Regressor (Ensemble)
    3. XGBoost Regressor (State-of-the-Art Gradient Boosting)
    4. Deep Neural Network (DNN)
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

    def train_dnn(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame = None, y_val: pd.Series = None, epochs: int = 100, batch_size: int = 32):
        """Trains a Deep Neural Network for bike demand regression."""

        # Convert data to NumPy arrays
        X_train_array = X_train.to_numpy(dtype=np.float32)
        y_train_array = y_train.to_numpy(dtype=np.float32)

        # Normalize input features using training data only
        normalizer = tf.keras.layers.Normalization(axis=-1)
        normalizer.adapt(X_train_array)

        # Build the Deep Neural Network
        model = tf.keras.Sequential([
            tf.keras.Input(shape=(X_train_array.shape[1],)),
            normalizer,
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(1, activation="linear")
        ])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss="mse",
            metrics=["mae"]
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss" if X_val is not None else "loss",
                patience=12,
                restore_best_weights=True
            )
        ]

        fit_kwargs = {
            "epochs": epochs,
            "batch_size": batch_size,
            "callbacks": callbacks,
            "verbose": 1
        }

        if X_val is not None and y_val is not None:
            fit_kwargs["validation_data"] = (
                X_val.to_numpy(dtype=np.float32),
                y_val.to_numpy(dtype=np.float32)
            )

        model.fit(X_train_array, y_train_array, **fit_kwargs)

        self.trained_models["DNN"] = model
        return model

    def save_model(self, model_name: str, filename: str = None) -> str:
        """Saves trained models using the appropriate format."""

        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} has not been trained yet.")

        model = self.trained_models[model_name]

        if filename is None:
            extension = ".keras" if model_name == "DNN" else ".joblib"
            filename = f"{model_name.lower().replace(' ', '_')}{extension}"

        filepath = os.path.join(self.models_dir, filename)

        if model_name == "DNN":
            model.save(filepath)
        else:
            joblib.dump(model, filepath)

        return filepath

    @staticmethod
    def load_model(filepath: str):
        """Loads model from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Saved model file not found at {filepath}")
        if filepath.endswith(".keras"):
            return tf.keras.models.load_model(filepath)
        return joblib.load(filepath)
