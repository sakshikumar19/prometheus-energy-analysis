"""
Converts a Prometheus JSON (.json.gz) file into a pandas DataFrame.

Usage:
    python prom_to_df.py path/to/file.json.gz
"""

import sys
import gzip
import json
import pandas as pd

def prom_to_df(file_path):
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("data", {}).get("result", [])
    rows = []

    for item in results:
        metric = item.get("metric", {})
        for ts, val in item.get("values", []):
            row = metric.copy()
            row["timestamp"] = float(ts)
            row["value"] = float(val)
            rows.append(row)

    df = pd.DataFrame(rows)

    if not df.empty:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")

    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prom_to_df.py path/to/file.json.gz")
        sys.exit(1)

    input_path = sys.argv[1]
    df = prom_to_df(input_path)

    print(f"\nLoaded {len(df)} rows from {input_path}\n")
    print(df.head())
