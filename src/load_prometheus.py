import gzip
import json
import pandas as pd

def normalize_instance_name(instance):
    if not instance:
        return instance
    if ':' in instance:
        parts = instance.rsplit(':', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
    return instance

def _open_prometheus_file(file_path):
    # Handle either plain .json or gzipped .json
    try:
        with open(file_path, "rb") as fb:
            magic = fb.read(2)
        is_gzip = magic == b"\x1f\x8b"
    except FileNotFoundError:
        raise

    if is_gzip:
        return gzip.open(file_path, "rt", encoding="utf-8")
    return open(file_path, "rt", encoding="utf-8")


def load_prometheus_file(file_path, aggregate=True, machine=None):
    with _open_prometheus_file(file_path) as f:
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
        df["instance_normalized"] = df["instance"].apply(normalize_instance_name)
        df = df[(df["instance"].str.contains(machine, na=False)) | 
                (df["instance_normalized"].str.contains(machine, na=False))]
        if "instance_normalized" in df.columns:
            df = df.drop(columns=["instance_normalized"])

    if aggregate and len(df) > 0:
        label_cols = [c for c in df.columns if c not in ["timestamp", "datetime", "value"]]
        if label_cols:
            if machine is None:
                df = df.groupby(["datetime"], as_index=False).agg({"value": "sum", "timestamp": "first"})
            else:
                df = df.groupby(["datetime"], as_index=False).agg({"value": "sum", "timestamp": "first"})

    return df[["datetime", "value"]].sort_values("datetime").reset_index(drop=True)