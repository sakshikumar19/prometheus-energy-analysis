import pandas as pd
import numpy as np

def _is_cumulative(df, metric_name=""):
    name_lower = metric_name.lower()
    if "cumulative" in name_lower or "_total" in name_lower or name_lower.endswith("_total"):
        return True
    if df.empty or len(df) < 2:
        return False
    sorted_df = df.sort_values("datetime")
    diffs = sorted_df["value"].diff()
    non_decreasing = (diffs >= 0).sum()
    return non_decreasing / len(diffs) > 0.95

def to_rate(df, metric_name=""):
    if df.empty or len(df) < 2:
        return df
    if not _is_cumulative(df, metric_name):
        return df
    
    df = df.sort_values("datetime").copy()
    dt_diff = df["datetime"].diff().dt.total_seconds()
    value_diff = df["value"].diff()
    
    rate = value_diff / dt_diff
    rate[rate < 0] = 0
    
    df["value"] = rate
    return df.dropna(subset=["value"]).reset_index(drop=True)

def infer_freq(df1, df2):
    if df1.empty or df2.empty:
        return "1s"
    
    diff1 = df1["datetime"].diff().median()
    diff2 = df2["datetime"].diff().median()
    freq_sec = min(diff1.total_seconds(), diff2.total_seconds())
    
    if freq_sec < 5:
        return "5s"
    elif freq_sec < 30:
        return "30s"
    elif freq_sec < 60:
        return "1min"
    else:
        return "1min"

def align_metrics(df1, df2, freq=None, tol=None):
    if df1.empty or df2.empty:
        return pd.DataFrame(columns=["datetime", "v1", "v2"])

    df1 = df1[["datetime", "value"]].rename(columns={"value": "v1"}).copy()
    df2 = df2[["datetime", "value"]].rename(columns={"value": "v2"}).copy()

    if freq is None:
        freq = infer_freq(df1, df2)

    df1 = df1.set_index("datetime").resample(freq).mean().reset_index()
    df2 = df2.set_index("datetime").resample(freq).mean().reset_index()

    if tol is None:
        tol = pd.Timedelta(freq) * 2

    merged = pd.merge_asof(
        df1.sort_values("datetime"),
        df2.sort_values("datetime"),
        on="datetime",
        tolerance=tol,
        direction="nearest"
    )

    merged = merged.dropna(subset=["v1", "v2"])
    return merged.reset_index(drop=True)
