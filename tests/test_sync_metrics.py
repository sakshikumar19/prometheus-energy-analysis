import pandas as pd
import numpy as np
from src.sync_metrics import to_rate, align_metrics, infer_freq, _is_cumulative

def test_is_cumulative_by_name():
    df = pd.DataFrame({"datetime": pd.date_range("2024-01-01", periods=5), "value": [1, 2, 3, 4, 5]})
    assert _is_cumulative(df, "metric_total") == True
    assert _is_cumulative(df, "metric_cumulative") == True
    assert _is_cumulative(df, "some_total") == True

def test_is_cumulative_by_behavior():
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=25),
        "value": list(range(10, 260, 10))
    })
    assert _is_cumulative(df, "regular_metric") == True

def test_is_cumulative_not_cumulative():
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=10),
        "value": [10, 5, 15, 8, 20, 12, 25, 18, 30, 22]
    })
    assert _is_cumulative(df, "regular_metric") == False

def test_to_rate_empty():
    df = pd.DataFrame(columns=["datetime", "value"])
    result = to_rate(df, "metric")
    assert result.empty

def test_to_rate_single_point():
    df = pd.DataFrame({"datetime": [pd.Timestamp("2024-01-01")], "value": [10]})
    result = to_rate(df, "metric")
    assert len(result) == 1

def test_to_rate_cumulative():
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="1s"),
        "value": [100, 200, 300, 400, 500]
    })
    result = to_rate(df, "metric_total")
    assert not result.empty
    assert len(result) == 4
    assert all(result["value"] >= 0)

def test_to_rate_non_cumulative():
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="1s"),
        "value": [10, 5, 15, 8, 20]
    })
    result = to_rate(df, "regular_metric")
    assert len(result) == 5
    assert result["value"].equals(df["value"])

def test_infer_freq():
    df1 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="60s")
    })
    df2 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="30s")
    })
    freq = infer_freq(df1, df2)
    assert "s" in freq
    assert int(freq.replace("s", "")) >= 60

def test_infer_freq_empty():
    df1 = pd.DataFrame(columns=["datetime"])
    df2 = pd.DataFrame(columns=["datetime"])
    freq = infer_freq(df1, df2)
    assert freq == "1s"

def test_align_metrics():
    df1 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="60s"),
        "value": [1, 2, 3, 4, 5]
    })
    df2 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="60s"),
        "value": [10, 20, 30, 40, 50]
    })
    aligned = align_metrics(df1, df2)
    assert not aligned.empty
    assert "v1" in aligned.columns
    assert "v2" in aligned.columns
    assert "datetime" in aligned.columns
    assert len(aligned) > 0

def test_align_metrics_different_freq():
    df1 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=3, freq="60s"),
        "value": [1, 2, 3]
    })
    df2 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=6, freq="30s"),
        "value": [10, 20, 30, 40, 50, 60]
    })
    aligned = align_metrics(df1, df2)
    assert not aligned.empty

def test_align_metrics_empty():
    df1 = pd.DataFrame(columns=["datetime", "value"])
    df2 = pd.DataFrame(columns=["datetime", "value"])
    aligned = align_metrics(df1, df2)
    assert aligned.empty

def test_align_metrics_custom_freq():
    df1 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="60s"),
        "value": [1, 2, 3, 4, 5]
    })
    df2 = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="60s"),
        "value": [10, 20, 30, 40, 50]
    })
    aligned = align_metrics(df1, df2, freq="120s")
    assert not aligned.empty

def test_to_rate_counter_reset():
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="1s"),
        "value": [100, 200, 300, 50, 150]
    })
    result = to_rate(df, "metric_total")
    assert not result.empty
    assert result["value"].min() >= 0
