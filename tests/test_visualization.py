import pandas as pd
import numpy as np
import tempfile
import os
import matplotlib
matplotlib.use('Agg')
from src.visualization import plot_12hr_scatter, plot_12hr_heatmap, _needs_log, _robust_limits

def test_needs_log():
    s = pd.Series([1, 10, 100, 1000, 10000])
    assert _needs_log(s) == True

def test_needs_log_false():
    s = pd.Series([1, 2, 3, 4, 5])
    assert _needs_log(s) == False

def test_needs_log_with_zeros():
    s = pd.Series([0, 1, 2, 3, 4])
    assert _needs_log(s) == False

def test_needs_log_empty():
    s = pd.Series([])
    assert _needs_log(s) == False

def test_robust_limits():
    s = pd.Series([1, 2, 3, 4, 5, 100, 200])
    limits = _robust_limits(s)
    assert limits is not None
    assert limits[0] < limits[1]

def test_robust_limits_empty():
    s = pd.Series([])
    limits = _robust_limits(s)
    assert limits is None

def test_robust_limits_single_value():
    s = pd.Series([5])
    limits = _robust_limits(s)
    assert limits is None

def test_plot_scatter_basic():
    df = pd.DataFrame({
        "v1": [1, 2, 3, 4, 5],
        "v2": [10, 20, 30, 40, 50]
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_scatter(df, path, "Metric1", "Metric2")
    assert os.path.exists(path)
    os.unlink(path)

def test_plot_scatter_empty():
    df = pd.DataFrame(columns=["v1", "v2"])
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_scatter(df, path, "Metric1", "Metric2")
    if os.path.exists(path):
        os.unlink(path)
    assert True

def test_plot_scatter_large_range():
    df = pd.DataFrame({
        "v1": [1, 10, 100, 1000, 10000],
        "v2": [1, 10, 100, 1000, 10000]
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_scatter(df, path, "Metric1", "Metric2")
    assert os.path.exists(path)
    os.unlink(path)

def test_plot_heatmap_basic():
    df = pd.DataFrame({
        "v1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "v2": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_heatmap(df, path, "Metric1", "Metric2")
    assert os.path.exists(path)
    os.unlink(path)

def test_plot_heatmap_empty():
    df = pd.DataFrame(columns=["v1", "v2"])
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_heatmap(df, path, "Metric1", "Metric2")
    if os.path.exists(path):
        os.unlink(path)
    assert True

def test_plot_heatmap_too_few_points():
    df = pd.DataFrame({
        "v1": [1, 2, 3],
        "v2": [10, 20, 30]
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_heatmap(df, path, "Metric1", "Metric2")
    if os.path.exists(path):
        os.unlink(path)
    assert True

def test_plot_heatmap_large_range():
    df = pd.DataFrame({
        "v1": [1, 10, 100, 1000, 10000] * 3,
        "v2": [1, 10, 100, 1000, 10000] * 3
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_heatmap(df, path, "Metric1", "Metric2")
    assert os.path.exists(path)
    os.unlink(path)

def test_plot_scatter_with_nans():
    df = pd.DataFrame({
        "v1": [1, 2, np.nan, 4, 5],
        "v2": [10, 20, 30, np.nan, 50]
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_scatter(df, path, "Metric1", "Metric2")
    assert os.path.exists(path)
    os.unlink(path)

def test_plot_heatmap_custom_bins():
    df = pd.DataFrame({
        "v1": range(20),
        "v2": range(20)
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    plot_12hr_heatmap(df, path, "Metric1", "Metric2", bins=50)
    assert os.path.exists(path)
    os.unlink(path)

