"""Run the quality contract against the committed sample using only Python's stdlib."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from uptime_lake.contracts import QUALITY_CHECKS, SENSOR_COLUMNS, anomaly_reasons, quality_reasons


def validate(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen: set[tuple[str, str]] = set()
    failures: Counter[str] = Counter()
    accepted: list[dict[str, float]] = []
    rejects: list[dict[str, object]] = []

    for row in rows:
        key = (row["index"], row["timestamp"])
        duplicate = key in seen
        seen.add(key)
        reasons = quality_reasons(row, duplicate=duplicate)
        failures.update(reasons)
        if reasons:
            rejects.append({"index": row["index"], "timestamp": row["timestamp"], "reasons": reasons})
            continue
        typed = {column.lower(): float(row[column]) for column in SENSOR_COLUMNS}
        accepted.append(typed)

    anomaly_count = sum(bool(anomaly_reasons(row)) for row in accepted)
    result = {
        "source_rows": len(rows),
        "silver_rows": len(accepted),
        "reject_rows": len(rejects),
        "reconciled": len(rows) == len(accepted) + len(rejects),
        "quality_checks": len(QUALITY_CHECKS),
        "failed_rows_by_check": {name: failures[name] for name in QUALITY_CHECKS},
        "anomaly_rows": anomaly_count,
        "sample_pass_rate_pct": round(len(accepted) / len(rows) * 100, 3),
    }
    if not result["reconciled"]:
        raise RuntimeError("Sample counts did not reconcile")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=REPO_ROOT / "data/sample/metropt3_sample.csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.path)
    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
