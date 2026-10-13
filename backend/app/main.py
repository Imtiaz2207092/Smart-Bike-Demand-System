import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models import Station, StationSnapshot
from app.routes.stations import router as station_router
from app.routes.snapshots import router as snapshot_router
from app.routes.status import router as status_router


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Smart Bicycle Demand Forecasting & Redistribution System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(station_router)
app.include_router(snapshot_router)

reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml_engine", "reports"))
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Smart Bike Demand System</title>
        <style>
            :root {
                --bg: #0f172a;
                --panel: #111827;
                --panel-2: #1f2937;
                --accent: #22c55e;
                --accent-2: #38bdf8;
                --text: #e5e7eb;
                --muted: #94a3b8;
                --danger: #f87171;
                --warn: #fbbf24;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0; font-family: Arial, sans-serif; background: linear-gradient(135deg, #020817, #0f172a 40%, #111827);
                color: var(--text); min-height: 100vh; padding: 24px;
            }
            .container { max-width: 1100px; margin: 0 auto; }
            h1 { margin-bottom: 8px; }
            .subtitle { color: var(--muted); margin-bottom: 24px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }
            .card {
                background: rgba(17, 24, 39, 0.9); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 14px; padding: 18px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.18);
            }
            .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
            .value { font-size: 28px; font-weight: 700; margin-top: 8px; }
            .section { margin-top: 28px; }
            table {
                width: 100%; border-collapse: collapse; background: rgba(17, 24, 39, 0.9); border-radius: 12px; overflow: hidden;
                border: 1px solid rgba(148, 163, 184, 0.2);
            }
            th, td { padding: 12px 14px; border-bottom: 1px solid rgba(148, 163, 184, 0.12); text-align: left; }
            th { background: rgba(30, 41, 59, 0.9); }
            .status-pill {
                display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700;
            }
            .status-shortage { background: rgba(248, 113, 113, 0.15); color: var(--danger); }
            .status-surplus { background: rgba(34, 197, 94, 0.12); color: var(--accent); }
            .status-balanced { background: rgba(56, 189, 248, 0.12); color: var(--accent-2); }
            .status-no_data { background: rgba(251, 191, 36, 0.15); color: var(--warn); }
            .api-link { color: var(--accent-2); text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Smart Bike Demand System</h1>
            <div class="subtitle">Machine learning forecast + redistribution monitoring dashboard</div>

            <div class="grid">
                <div class="card">
                    <div class="label">System status</div>
                    <div class="value" id="system-status">Running</div>
                </div>
                <div class="card">
                    <div class="label">Stations monitored</div>
                    <div class="value" id="stations-count">-</div>
                </div>
                <div class="card">
                    <div class="label">Balanced</div>
                    <div class="value" id="balanced-count">-</div>
                </div>
                <div class="card">
                    <div class="label">Shortage</div>
                    <div class="value" id="shortage-count">-</div>
                </div>
            </div>

            <div class="section">
                <h2>Station status</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Station</th>
                            <th>Capacity</th>
                            <th>Available bikes</th>
                            <th>Bike %</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="station-table-body"></tbody>
                </table>
            </div>

            <div class="section">
                <h2>Model comparison</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>MAE</th>
                            <th>RMSE</th>
                            <th>MAPE (%)</th>
                            <th>R²</th>
                        </tr>
                    </thead>
                    <tbody id="model-table-body"></tbody>
                </table>
            </div>

            <div class="section">
                <p>API docs: <a class="api-link" href="/docs">/docs</a></p>
            </div>
        </div>

        <script>
            async function loadStationData() {
                const response = await fetch('/stations/status');
                const stations = await response.json();

                const tableBody = document.getElementById('station-table-body');
                let shortage = 0; let balanced = 0; let total = 0;
                tableBody.innerHTML = '';

                stations.forEach(station => {
                    total += 1;
                    if (station.status === 'shortage') shortage += 1;
                    if (station.status === 'balanced') balanced += 1;

                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${station.station_name || station.station_id}</td>
                        <td>${station.capacity ?? '-'}</td>
                        <td>${station.available_bikes ?? '-'}</td>
                        <td>${station.bike_percentage ?? '-'}%</td>
                        <td><span class="status-pill status-${station.status || 'no_data'}">${station.status || 'no_data'}</span></td>
                    `;
                    tableBody.appendChild(row);
                });

                document.getElementById('stations-count').textContent = total;
                document.getElementById('balanced-count').textContent = balanced;
                document.getElementById('shortage-count').textContent = shortage;
                document.getElementById('system-status').textContent = 'Running';
            }

            async function loadModelData() {
                const response = await fetch('/reports/model_comparison.json');
                const models = await response.json();
                const body = document.getElementById('model-table-body');
                body.innerHTML = models.map(model => `
                    <tr>
                        <td>${model.Model}</td>
                        <td>${model.MAE}</td>
                        <td>${model.RMSE}</td>
                        <td>${model['MAPE (%)']}</td>
                        <td>${model.R2_Score}</td>
                    </tr>
                `).join('');
            }

            loadStationData();
            loadModelData();
            setInterval(loadStationData, 15000);
        </script>
    </body>
    </html>
    """