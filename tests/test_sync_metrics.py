import pandas as pd
from src.sync_metrics import align_metrics

def test_align_metrics_nearest():
    t1 = pd.date_range("2024-01-01", periods=3, freq="1s")
    t2 = pd.date_range("2024-01-01 00:00:00.5", periods=3, freq="1s")
    df1 = pd.DataFrame({"datetime": t1, "value": [1,2,3]})
    df2 = pd.DataFrame({"datetime": t2, "value": [10,20,30]})
    aligned = align_metrics(df1, df2, tol="1s")
    assert len(aligned) == 3
    assert "v1" in aligned and "v2" in aligned
