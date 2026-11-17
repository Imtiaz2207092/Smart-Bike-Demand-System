# Smart Bike Demand System

A secure smart bike sharing demand forecasting and redistribution system.

## Team Members

- Imtiaj Ahmad — 2207092
- Yasar Wajih — 2207064

## Main Features

- Demand Prediction
- Station-wise Demand Prediction
- Peak Hour Detection
- Shortage Detection
- Surplus Detection
- Redistribution Recommendation
- Distance-aware Redistribution
- Model Monitoring
- Secure Dashboard

To run this project backend:
D:
cd Smart-Bike-Demand-System\backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload

To run this project frontend:
D:
cd Smart-Bike-Demand-System\vite
npm run dev

## Model evaluation graphs

From the project root, install the ML requirements and run the training/evaluation
pipeline to regenerate the holdout metrics, graph images, and standalone report:

```powershell
python -m pip install -r ml_engine/requirements.txt
python -m ml_engine.main
```

Open `ml_engine/reports/model_report.html` in any browser. The report embeds its
charts, so it works offline and does not need a local web server. Individual PNG
charts are saved in `ml_engine/reports/figures/`; `model_comparison.md` and
`model_comparison.json` contain the same run's metric results.

cycleflow_user password: Y@$Ar&1m7IA^