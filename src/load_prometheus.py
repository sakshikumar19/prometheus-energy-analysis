import gzip
import json
import pandas as pd

def load_prometheus_file(file_path):
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
