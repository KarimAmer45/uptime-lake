"""Source contract and pure-Python quality rules used by tests and local validation."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

SOURCE_COLUMNS = (
    "index",
    "timestamp",
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses",
)

PRESSURE_COLUMNS = ("TP2", "TP3", "H1", "DV_pressure", "Reservoirs")
BINARY_COLUMNS = ("COMP", "DV_eletric", "Towers", "MPG", "LPS", "Pressure_switch", "Oil_level")
SENSOR_COLUMNS = SOURCE_COLUMNS[2:]
QUALITY_CHECKS = (
    "invalid_reading_id",
    "invalid_timestamp",
    "timestamp_outside_expected_window",
    "missing_required_sensor",
    "pressure_out_of_range",
    "oil_temperature_out_of_range",
    "motor_current_out_of_range",
    "invalid_binary_signal",
    "negative_caudal_impulses",
    "duplicate_reading",
)


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def quality_reasons(row: Mapping[str, str], duplicate: bool = False) -> list[str]:
    """Evaluate the row-level contract without Spark for fast deterministic tests."""
    reasons: list[str] = []
    try:
        int(row.get("index", ""))
    except (TypeError, ValueError):
        reasons.append("invalid_reading_id")

    event_ts = _timestamp(row.get("timestamp"))
    if event_ts is None:
        reasons.append("invalid_timestamp")
    elif not datetime(2020, 1, 1) <= event_ts < datetime(2021, 1, 1):
        reasons.append("timestamp_outside_expected_window")

    parsed = {column: _float(row.get(column)) for column in SENSOR_COLUMNS}
    if any(value is None for value in parsed.values()):
        reasons.append("missing_required_sensor")
    if any(parsed[column] is not None and not -2 <= parsed[column] <= 20 for column in PRESSURE_COLUMNS):
        reasons.append("pressure_out_of_range")
    oil = parsed["Oil_temperature"]
    if oil is not None and not -30 <= oil <= 150:
        reasons.append("oil_temperature_out_of_range")
    motor = parsed["Motor_current"]
    if motor is not None and not -1 <= motor <= 50:
        reasons.append("motor_current_out_of_range")
    if any(parsed[column] is not None and parsed[column] not in (0.0, 1.0) for column in BINARY_COLUMNS):
        reasons.append("invalid_binary_signal")
    caudal = parsed["Caudal_impulses"]
    if caudal is not None and caudal < 0:
        reasons.append("negative_caudal_impulses")
    if duplicate:
        reasons.append("duplicate_reading")
    return reasons


def anomaly_reasons(row: Mapping[str, float]) -> list[str]:
    """Return explainable operating-risk flags used by the Gold layer."""
    reasons: list[str] = []
    if row["oil_temperature"] > 100:
        reasons.append("high_oil_temperature")
    if row["motor_current"] > 12:
        reasons.append("high_motor_current")
    if abs(row["tp3"] - row["reservoirs"]) > 1.5:
        reasons.append("reservoir_pressure_mismatch")
    if row["lps"] == 1:
        reasons.append("low_pressure_switch_active")
    if row["oil_level"] == 1:
        reasons.append("low_oil_level_signal")
    return reasons

