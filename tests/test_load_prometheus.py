import pandas as pd
from src.load_prometheus import load_prometheus_file
import gzip, json, tempfile

def make_test_prom_file():
    sample = {
        "data": {
            "result": [
                {
                    "metric": {"__name__": "disk_io"},
                    "values": [[1, "10"], [2, "20"]],
                }
            ]
        }
    }
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".json.gz")
    with gzip.open(f.name, "wt", encoding="utf-8") as g:
        json.dump(sample, g)
    return f.name

def test_load_prometheus_file_basic():
    path = make_test_prom_file()
    df = load_prometheus_file(path)
    assert not df.empty
    assert "timestamp" in df.columns
    assert "value" in df.columns
    assert "datetime" in df.columns