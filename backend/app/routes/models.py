import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/models", tags=["Model Evaluation"])
REPORT_PATH = Path(__file__).resolve().parents[3] / "ml_engine" / "reports" / "model_comparison.json"


@router.get("/comparison")
def get_model_comparison():
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="The ML model comparison report is unavailable. Run the ML evaluation pipeline first.",
        ) from exc
