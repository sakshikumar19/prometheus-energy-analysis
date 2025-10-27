# Prometheus Energy Profiler

A toolkit for analyzing energy consumption patterns and system load metrics from Prometheus monitoring data, with a focus on HPC scheduler evaluation and energy efficiency.

## Overview

This project provides reusable scripts to:

- Analyze correlations between system load and power consumption
- Visualize temporal trends in energy usage
- Profile efficiency metrics across different operational states
- Support CERN energy monitoring and scheduler profiling initiatives

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

**1. Analyze metric pairs (correlation analysis)**

```bash
python src/analyze_pair.py \
  --metric1 node_load1 \
  --metric2 rPDULoadStatusLoad \
  --num-files 5 \
  --output outputs/figs/correlation.png
```

**2. Generate metric visualizations**

```bash
python src/visualization.py \
  --metric1 node_load1 \
  --num-files 5 \
  --single

python src/visualization.py \
  --metric1 node_load1 \
  --metric2 rPDULoadStatusLoad \
  --num-files 5 \
  --window 12
```

**3. Run efficiency analysis**

```bash
python src/efficiency_analysis.py \
  --load-metric node_load1 \
  --power-metric rPDULoadStatusLoad \
  --num-files 5
```

**4. Complete EDA report**

```bash
python src/eda_report.py \
  --num-files 5 \
  --metrics node_load1 node_procs_running rPDULoadStatusLoad
```

## 📁 Project Structure

```
prometheus-energy-profiler/
├── src/              # Analysis scripts
├── data/             # Prometheus metric data (gzipped JSON)
├── notebooks/        # Jupyter notebooks for exploration
├── outputs/
│   ├── figs/        # Generated visualizations
│   └── logs/        # Analysis logs
└── docs/            # Documentation
```

## 📊 Available Metrics

- `node_load1`: System 1-minute load average
- `node_procs_running`: Number of running processes
- `rPDULoadStatusLoad`: PDU power load measurements

## 🔧 Script Parameters

All scripts support:

- `--num-files N`: Limit data files processed (default: 3, reduces runtime)
- `--output PATH`: Custom output location
- `--verbose`: Detailed logging

## 📄 License

Apache 2.0 - See LICENSE file
