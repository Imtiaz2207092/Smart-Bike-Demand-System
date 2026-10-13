"""
Model Comparison and Evaluation Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calculates MAE, RMSE, MAPE, and R2 score."""
    y_pred = np.clip(y_pred, a_min=0, a_max=None)
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    non_zero_mask = y_true > 0
    if np.sum(non_zero_mask) > 0:
        mape = np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100
    else:
        mape = 0.0
        
    return {
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "MAPE (%)": round(float(mape), 2),
        "R2_Score": round(float(r2), 4)
    }

def evaluate_and_compare_models(models_dict: dict, X_test: pd.DataFrame, y_test: pd.Series, reports_dir: str = "ml_engine/reports") -> pd.DataFrame:
    """
    Evaluates trained models on test set and generates markdown/json reports.
    """
    os.makedirs(reports_dir, exist_ok=True)
    results = []

    for name, model in models_dict.items():
        y_pred = model.predict(X_test)
        metrics = calculate_metrics(y_test.values, y_pred)
        metrics["Model"] = name
        results.append(metrics)

    comparison_df = pd.DataFrame(results)[["Model", "MAE", "RMSE", "MAPE (%)", "R2_Score"]]
    comparison_df = comparison_df.sort_values(by="RMSE", ascending=True).reset_index(drop=True)

    json_path = os.path.join(reports_dir, "model_comparison.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_df.to_dict(orient="records"), f, indent=4)

    md_path = os.path.join(reports_dir, "model_comparison.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# ML Model Comparison & Performance Report\n\n")
        f.write(f"**Developer:** Imtiaj Ahmad (Roll: 2207092)\n\n")
        f.write(comparison_df.to_markdown(index=False))
        f.write("\n\n*Best performing model selected based on lowest RMSE and highest R² Score.*")

    return comparison_df
