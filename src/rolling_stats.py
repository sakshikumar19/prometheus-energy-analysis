import pandas as pd
import numpy as np

def rolling_corr(df, window=30, min_periods=None):
    if df.empty:
        return pd.DataFrame()

    out = df[["datetime", "v1", "v2"]].copy().sort_values("datetime").reset_index(drop=True)

    if min_periods is None:
        min_periods = max(3, window // 3)

    out["v1_roll"] = out["v1"].rolling(window=window, min_periods=min_periods).mean()
    out["v2_roll"] = out["v2"].rolling(window=window, min_periods=min_periods).mean()

    roll_corrs = []
    for i in range(len(out)):
        start = max(0, i - window + 1)
        end = i + 1
        window_data = out.iloc[start:end][["v1", "v2"]].dropna()
        if len(window_data) >= min_periods:
            corr = window_data["v1"].corr(window_data["v2"])
            roll_corrs.append(corr)
        else:
            roll_corrs.append(np.nan)

    out["roll_corr"] = roll_corrs
    return out
