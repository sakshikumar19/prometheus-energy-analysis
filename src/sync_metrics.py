import pandas as pd

def align_metrics(df1, df2, how="nearest", freq=None, tol="1s"):
    if freq:
        df1 = df1.set_index("datetime").resample(freq).mean().reset_index()
        df2 = df2.set_index("datetime").resample(freq).mean().reset_index()

    df1 = df1[["datetime", "value"]].rename(columns={"value": "v1"})
    df2 = df2[["datetime", "value"]].rename(columns={"value": "v2"})

    if how == "nearest":
        merged = pd.merge_asof(
            df1.sort_values("datetime"),
            df2.sort_values("datetime"),
            on="datetime",
            tolerance=pd.Timedelta(tol),
            direction="nearest"
        )
    else:
        merged = pd.merge(df1, df2, on="datetime", how="inner")

    merged = merged.dropna()
    return merged
