from pathlib import Path
import sys

import pandas as pd

# Resolve the repository root so the existing ML engine can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_engine.src.forecaster import DemandForecaster


_model_path = PROJECT_ROOT / "ml_engine" / "models_saved" / "xgboost.joblib"
_forecaster = None


def get_forecaster() -> DemandForecaster:
    """Load the trained model once and reuse it."""
    global _forecaster

    if _forecaster is None:
        _forecaster = DemandForecaster(model_path=str(_model_path))

    return _forecaster


def predict_demand(input_data: dict) -> dict:
    """Validate the supplied forecast inputs and predict bike demand."""
    required_fields = [
        "datetime",
        "season",
        "holiday",
        "workingday",
        "weather",
        "temp",
        "atemp",
        "humidity",
        "windspeed",
    ]

    missing_fields = [
        field for field in required_fields
        if field not in input_data or input_data[field] is None
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required forecast fields: {', '.join(missing_fields)}"
        )

    try:
        forecast_input = dict(input_data)
        forecast_input["datetime"] = pd.to_datetime(
            forecast_input["datetime"], errors="raise"
        ).to_pydatetime()

        result = get_forecaster().predict_single(forecast_input)

        return {
            "predicted_demand": result["predicted_demand"],
            "is_peak_hour": result["is_peak_hour"],
            "datetime": forecast_input["datetime"].isoformat(),
        }
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid forecast input: {exc}") from exc
