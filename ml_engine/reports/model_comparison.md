# ML Model Comparison & Performance Report

**Developer:** Imtiaj Ahmad (Roll: 2207092)

| Model             |     MAE |      MSE |     RMSE |   MAPE (%) |   R2_Score |
|:------------------|--------:|---------:|---------:|-----------:|-----------:|
| XGBoost           | 44.004  |  4455.48 |  66.7494 |      32.85 |     0.9014 |
| DNN               | 47.9158 |  4683.57 |  68.4366 |      53.09 |     0.8964 |
| Random Forest     | 55.3025 |  6971.99 |  83.4985 |      27.06 |     0.8458 |
| Linear Regression | 89.9683 | 14620    | 120.913  |     181.06 |     0.6766 |

*Best model ranked by lowest RMSE; higher R² is also better.*

Open [the standalone visual report](model_report.html) for prediction, residual, training-loss, and feature-gain charts.