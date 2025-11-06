import pandas as pd
import numpy as np
from src.correlations import compute_correlations, _normalize

def test_compute_correlations_perfect():
    df = pd.DataFrame({
        "v1": [1, 2, 3, 4, 5],
        "v2": [2, 4, 6, 8, 10]
    })
    result = compute_correlations(df)
    assert result is not None
    assert abs(result["pearson_r"] - 1.0) < 0.001
    assert abs(result["spearman_r"] - 1.0) < 0.001
    assert result["n"] == 5

def test_compute_correlations_negative():
    df = pd.DataFrame({
        "v1": [1, 2, 3, 4, 5],
        "v2": [10, 8, 6, 4, 2]
    })
    result = compute_correlations(df)
    assert result is not None
    assert result["pearson_r"] < 0
    assert result["n"] == 5

def test_compute_correlations_no_correlation():
    df = pd.DataFrame({
        "v1": [1, 2, 3, 4, 5],
        "v2": [5, 2, 4, 1, 3]
    })
    result = compute_correlations(df)
    assert result is not None
    assert abs(result["pearson_r"]) <= 0.5

def test_compute_correlations_empty():
    df = pd.DataFrame(columns=["v1", "v2"])
    result = compute_correlations(df)
    assert result is None

def test_compute_correlations_with_nans():
    df = pd.DataFrame({
        "v1": [1, 2, np.nan, 4, 5],
        "v2": [2, 4, 6, 8, 10]
    })
    result = compute_correlations(df)
    assert result is not None
    assert result["n"] == 4

def test_compute_correlations_normalized():
    df = pd.DataFrame({
        "v1": [100, 200, 300, 400, 500],
        "v2": [10, 20, 30, 40, 50]
    })
    result = compute_correlations(df, use_norm=True)
    assert result is not None
    assert abs(result["pearson_r"] - 1.0) < 0.001

def test_normalize():
    s = pd.Series([1, 2, 3, 4, 5])
    normalized = _normalize(s)
    assert normalized.std() == 1.0
    assert abs(normalized.mean()) < 0.001

def test_normalize_zero_std():
    s = pd.Series([5, 5, 5, 5, 5])
    normalized = _normalize(s)
    assert normalized.equals(s)

def test_compute_correlations_many_points():
    np.random.seed(42)
    df = pd.DataFrame({
        "v1": np.random.randn(100),
        "v2": np.random.randn(100)
    })
    result = compute_correlations(df)
    assert result is not None
    assert result["n"] == 100
    assert abs(result["pearson_r"]) < 0.5

def test_compute_correlations_with_missing_v2():
    df = pd.DataFrame({
        "v1": [1, 2, 3, 4, 5],
        "v2": [2, np.nan, 6, 8, 10]
    })
    result = compute_correlations(df)
    assert result is not None
    assert result["n"] == 4
