import pandas as pd
import json
import gzip
import tempfile
import os
import matplotlib
matplotlib.use('Agg')
from src.analyze_pair import analyze_pair

def make_test_json(file_path, instance_name="test_host"):
    base_time = 1754002800
    values = []
    for i in range(15):
        values.append([base_time + i * 60, str(10 + i * 10)])
    data = {
        "data": {
            "result": [
                {
                    "metric": {"instance": instance_name},
                    "values": values
                }
            ]
        }
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)

def test_analyze_pair_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "test_host")
        make_test_json(file2, "test_host")
        
        result = analyze_pair("test_host", file1, file2, "Metric1", "Metric2", outdir=tmpdir)
        assert result is not None
        assert "dir" in result
        assert "correlation" in result
        assert "windowed_data" in result
        assert os.path.exists(os.path.join(result["dir"], "scatter.png"))
        assert os.path.exists(os.path.join(result["dir"], "heatmap.png"))
        assert os.path.exists(os.path.join(result["dir"], "notes.txt"))

def test_analyze_pair_no_matching_machine():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "host1")
        make_test_json(file2, "host1")
        
        result = analyze_pair("host2", file1, file2, "Metric1", "Metric2", outdir=tmpdir)
        assert result is None

def test_analyze_pair_with_window():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "test_host")
        make_test_json(file2, "test_host")
        
        result = analyze_pair("test_host", file1, file2, "Metric1", "Metric2", 
                            outdir=tmpdir, window_start=None, window_end=None, hours=1)
        assert result is not None

def test_analyze_pair_with_hours():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "test_host")
        make_test_json(file2, "test_host")
        
        result = analyze_pair("test_host", file1, file2, "Metric1", "Metric2", 
                            outdir=tmpdir, hours=6)
        assert result is not None

def test_analyze_pair_empty_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        empty_data = {"data": {"result": []}}
        with open(file1, 'w') as f:
            json.dump(empty_data, f)
        with open(file2, 'w') as f:
            json.dump(empty_data, f)
        
        result = analyze_pair("test_host", file1, file2, "Metric1", "Metric2", outdir=tmpdir)
        assert result is None

def test_analyze_pair_notes_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "test_host")
        make_test_json(file2, "test_host")
        
        result = analyze_pair("test_host", file1, file2, "Metric1", "Metric2", outdir=tmpdir)
        
        notes_path = os.path.join(result["dir"], "notes.txt")
        assert os.path.exists(notes_path)
        
        with open(notes_path, 'r') as f:
            content = f.read()
            assert "Machine: test_host" in content
            assert "Metric 1: Metric1" in content
            assert "Metric 2: Metric2" in content

def test_analyze_pair_cumulative_metric():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "test_host")
        make_test_json(file2, "test_host")
        
        result = analyze_pair("test_host", file1, file2, "Power Usage Cumulative", "Load", outdir=tmpdir)
        assert result is not None

def test_analyze_pair_directory_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        
        make_test_json(file1, "test_host")
        make_test_json(file2, "test_host")
        
        result = analyze_pair("test_host", file1, file2, "Metric1", "Metric2", outdir=tmpdir)
        assert os.path.exists(result["dir"])

