import pandas as pd
from src.correlations import compute_correlations

def test_compute_correlations_basic():
    df = pd.DataFrame({"v1": [1,2,3,4,5], "v2": [2,4,6,8,10]})
    res = compute_correlations(df)
    assert abs(res["pearson_r"] - 1) < 1e-6
    assert res["n"] == 5
