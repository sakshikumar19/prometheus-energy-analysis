import gzip
import json
import pandas as pd

def load_prometheus_file(file_path, aggregate=True, machine=None):
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

    if machine is not None and "instance" in df.columns:
        df = df[df["instance"].str.contains(machine, na=False)]

    if aggregate and len(df) > 0:
        label_cols = [c for c in df.columns if c not in ["timestamp", "datetime", "value"]]
        if label_cols:
            if machine is None:
                df = df.groupby(["datetime"], as_index=False).agg({"value": "sum", "timestamp": "first"})
            else:
                df = df.groupby(["datetime"], as_index=False).agg({"value": "sum", "timestamp": "first"})

    return df[["datetime", "value"]].sort_values("datetime").reset_index(drop=True)

def list_machines(file_path):
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("data", {}).get("result", [])
    machines = set()

    for item in results:
        metric = item.get("metric", {})
        if "instance" in metric:
            instance = metric["instance"]
            machines.add(instance)

    return sorted(list(machines))
