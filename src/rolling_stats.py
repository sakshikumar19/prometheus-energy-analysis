import pandas as pd

def rolling_corr(df, window=5):
    out = df[["datetime", "v1", "v2"]].copy()
    out["v1_roll"] = out["v1"].rolling(window).mean()
    out["v2_roll"] = out["v2"].rolling(window).mean()
    out["roll_corr"] = out["v1"].rolling(window).corr(out["v2"])
    return out
