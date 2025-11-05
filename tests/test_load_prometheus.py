import pandas as pd
import json
import gzip
import tempfile
import os
from src.load_prometheus import load_prometheus_file, normalize_instance_name

def test_normalize_instance_name():
    assert normalize_instance_name("host:9100") == "host"
    assert normalize_instance_name("host:8080") == "host"
    assert normalize_instance_name("host") == "host"
    assert normalize_instance_name("") == ""
    assert normalize_instance_name(None) == None

def test_load_prometheus_json():
    data = {
        "data": {
            "result": [
                {
                    "metric": {"instance": "host1", "__name__": "metric1"},
                    "values": [[1000, "10"], [2000, "20"], [3000, "30"]]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    
    df = load_prometheus_file(path)
    assert not df.empty
    assert len(df) == 3
    assert "datetime" in df.columns
    assert "value" in df.columns
    
    os.unlink(path)

def test_load_prometheus_gzip():
    data = {
        "data": {
            "result": [
                {
                    "metric": {"instance": "host1"},
                    "values": [[1000, "5"], [2000, "15"]]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.json.gz', delete=False) as f:
        with gzip.open(f, 'wt') as g:
            json.dump(data, g)
        path = f.name
    
    df = load_prometheus_file(path)
    assert not df.empty
    assert len(df) == 2
    
    os.unlink(path)

def test_load_prometheus_with_machine_filter():
    data = {
        "data": {
            "result": [
                {
                    "metric": {"instance": "host1.example.com:9100"},
                    "values": [[1000, "10"], [2000, "20"]]
                },
                {
                    "metric": {"instance": "host2.example.com:9100"},
                    "values": [[1000, "5"], [2000, "15"]]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    
    df = load_prometheus_file(path, machine="host1")
    assert not df.empty
    assert len(df) == 2
    
    os.unlink(path)

def test_load_prometheus_csv():
    df_csv = pd.DataFrame({
        "machine": ["host1", "host2"],
        "1754002800": [100.5, 200.3],
        "1754006400": [150.2, 250.1]
    })
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df_csv.to_csv(f.name, index=False)
        path = f.name
    
    df = load_prometheus_file(path, machine="host1")
    assert not df.empty
    assert "datetime" in df.columns
    assert "value" in df.columns
    
    os.unlink(path)

def test_load_prometheus_empty():
    data = {"data": {"result": []}}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    
    df = load_prometheus_file(path)
    assert df.empty
    
    os.unlink(path)

def test_load_prometheus_missing_file():
    try:
        load_prometheus_file("nonexistent.json")
        assert False
    except FileNotFoundError:
        assert True
