import gzip
import json
import pandas as pd

def load_prometheus_file(file_path, aggregate=True):
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

    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")

    if aggregate and len(df) > 0:
        label_cols = [c for c in df.columns if c not in ["timestamp", "datetime", "value"]]
        if label_cols:
            df = df.groupby(["datetime"], as_index=False).agg({"value": "sum", "timestamp": "first"})

    return df[["datetime", "value"]].sort_values("datetime").reset_index(drop=True)
