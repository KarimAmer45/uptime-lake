"""Download the licensed MetroPT-3 archive from UCI and verify its row count."""

from __future__ import annotations

import argparse
import csv
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/791/metropt%2B3%2Bdataset.zip"
CSV_NAME = "MetroPT3(AirCompressor).csv"
EXPECTED_ROWS = 1_516_948


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / CSV_NAME

    with tempfile.TemporaryDirectory(prefix="metropt3-") as temp_dir:
        archive = Path(temp_dir) / "metropt3.zip"
        print(f"Downloading {URL}")
        urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as zipped:
            members = {Path(name).name: name for name in zipped.namelist()}
            if CSV_NAME not in members:
                raise RuntimeError(f"{CSV_NAME} not found; archive contains {sorted(members)}")
            with zipped.open(members[CSV_NAME]) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)

    with destination.open(encoding="utf-8", newline="") as handle:
        row_count = sum(1 for _ in csv.reader(handle)) - 1
    if row_count != EXPECTED_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_ROWS:,} rows, found {row_count:,}")
    print(f"Verified {destination}: {row_count:,} data rows")


if __name__ == "__main__":
    main()

