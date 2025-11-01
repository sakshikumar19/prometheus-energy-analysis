import pandas as pd
from src.rolling_stats import rolling_corr

def test_rolling_corr_shape():
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=10, freq="s"),
        "v1": range(10),
        "v2": range(0,20,2)
    })
    out = rolling_corr(df, window=3)
    assert "roll_corr" in out.columns
    assert len(out) == 10
