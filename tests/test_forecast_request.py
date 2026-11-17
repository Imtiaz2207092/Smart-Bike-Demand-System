import pytest
from pydantic import ValidationError

from app.routes.forecasts import ForecastRequest


def forecast_payload(**overrides):
    return {
        "datetime": "2026-11-06T08:00:00",
        "season": 4,
        "holiday": 0,
        "workingday": 1,
        "weather": 1,
        "temp": 20.5,
        "atemp": 24.24,
        "humidity": 60,
        "windspeed": 13,
        **overrides,
    }


def test_forecast_request_accepts_training_data_scale_values():
    request = ForecastRequest.model_validate(forecast_payload())

    assert request.temp == 20.5
    assert request.atemp == 24.24
    assert request.windspeed == 13


def test_forecast_request_accepts_training_data_upper_bounds():
    request = ForecastRequest.model_validate(
        forecast_payload(temp=56, atemp=60, windspeed=60)
    )

    assert request.temp == 41
    assert request.atemp == 50
    assert request.windspeed == 56.9969


@pytest.mark.parametrize(
    ("field", "value"),
    [("temp", 41.1), ("atemp", 50.1), ("windspeed", 56.997)],
)
def test_forecast_request_rejects_values_above_dataset_scale(field, value):
    with pytest.raises(ValidationError):
        ForecastRequest.model_validate(forecast_payload(**{field: value}))
