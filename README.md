# Prometheus Energy Profiler

This repository provides a workflow to compare two Prometheus time series for a selected machine over a given time window. It aligns the series in time, computes correlation statistics and generates standard visualizations (scatter and heatmap) together with a brief run summary.

## Dataset

Input files (Prometheus JSON or JSON.GZ) should be placed under `data/`.
The dataset used in the experiments is publicly available:

- 2025 Aug Week 1: https://github.com/UofM-Green-Compute/2025_Aug_wk1_Data

Download the required files from the dataset into your local `data/` folder. The loader supports both `.json.gz` and plain `.json` files.

## Installation

- Python 3.10+
- Install dependencies (activate a virtual environment if desired):

```bash
pip install -r requirements.txt
```

## Usage (per-machine pair analysis)

The command below writes results to `results/<machine>/<metric1>_vs_<metric2>/<window>/` (plots and notes):

```bash
python -m src.cli.run_pair_analysis \
  --file1 data/cleaned_raw_by_metric_powerUsageCumulativeWattage_1753999200.0.json \
  --file2 data/node_load1/1754002800.0.json.gz \
  --machine wn1205080 \
  --metric1 "Power Usage Cumulative" \
  --metric2 "Load (1m)" \
  --start 2025-07-31T23:00:00Z \
  --end   2025-08-01T11:00:00Z \
  --outdir results
```

Notes:
- `--machine` performs a substring match against the Prometheus `instance` (e.g., `wn1205080`).
- Both `.json` and `.json.gz` inputs are supported.
- Alternatively, omit `--start/--end` and use `--hours N` to select the last N hours.

## Method

- Parse two Prometheus matrix responses (`data.result[].values`).
- Filter rows for the target machine (substring match on `instance`, plus host-only normalization).
- Align timestamps shared by both series.
- Compute Pearson and Spearman correlations.
- Save a scatter plot and a 2D density heatmap for the selected window.

## Troubleshooting

If the script prints "No results (empty or unaligned data)", verify:
- `--machine` matches the `instance` string in both files.
- The two series overlap in time for the selected window.
- The input follows Prometheus matrix JSON format (`data.result[].values`).

## AI Assistance

During development, I employed a locally configured AI assistant tuned with the following SYSTEM PROMPT:

> *“You are a code auditor. Provide micro-suggestions focused on clarity, naming consistency, structure, layout and minor completeness gaps. Avoid major refactors or architectural changes.”*

This setup allowed the AI to consistently provide concise, review-style feedback on test-suite structure for the analysis pipeline and coverage checks for edge cases (like empty or malformed Prometheus result arrays)
