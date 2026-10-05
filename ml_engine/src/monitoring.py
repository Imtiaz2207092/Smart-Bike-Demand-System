"""
Model Performance Monitoring & Drift Detection Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import numpy as np
import pandas as pd
from ml_engine.src.evaluation import calculate_metrics

class ModelPerformanceMonitor:
    """Monitors live model performance and drift."""

    def __init__(self, error_threshold_mae: float = 35.0, warning_threshold_mae: float = 25.0):
        self.error_threshold_mae = error_threshold_mae
        self.warning_threshold_mae = warning_threshold_mae

    def evaluate_live_performance(self, actual: pd.Series, predicted: pd.Series) -> dict:
        y_true = actual.values
        y_pred = predicted.values
        
        metrics = calculate_metrics(y_true, y_pred)
        mae = metrics["MAE"]
        
        if mae > self.error_threshold_mae:
            status = "DEGRADED"
            alert_msg = f"CRITICAL: MAE ({mae}) exceeded threshold ({self.error_threshold_mae})."
        elif mae > self.warning_threshold_mae:
            status = "WARNING"
            alert_msg = f"WARNING: MAE ({mae}) is approaching threshold ({self.warning_threshold_mae})."
        else:
            status = "HEALTHY"
            alert_msg = f"HEALTHY: Model performing well with MAE = {mae}."

        return {
            "status": status,
            "message": alert_msg,
            "metrics": metrics,
            "sample_count": len(actual)
        }
