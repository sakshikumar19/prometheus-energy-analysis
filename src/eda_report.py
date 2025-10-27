#!/usr/bin/env python3
"""
Generate a comprehensive EDA report for all available metrics.

Usage:
    python eda_report.py --num-files 2
"""

import argparse
import gzip
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats


def get_data_span_info(metric_name, data_dir, num_files=3):
    """Return number of files loaded and time span (days and hours)."""
    metric_path = Path(data_dir) / metric_name
    files = sorted(list(metric_path.glob("*.json.gz")))[:num_files]
    n_files = len(files)

    df = pd.DataFrame()
    for file_path in files:
        with gzip.open(file_path, 'rt') as f:
            data = json.load(f)
            if 'data' in data and 'result' in data['data']:
                for result in data['data']['result']:
                    if 'values' in result:
                        temp_df = pd.DataFrame(result['values'], columns=['timestamp', 'value'])
                        temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'], unit='s')
                        df = pd.concat([df, temp_df], ignore_index=True)

    if df.empty:
        return n_files, None, None, None

    start_time, end_time = df['timestamp'].min(), df['timestamp'].max()
    total_hours = (end_time - start_time).total_seconds() / 3600
    total_days = total_hours / 24
    return n_files, start_time, end_time, (round(total_days, 2), round(total_hours, 2))


def load_metric_data(metric_name, data_dir, num_files=3):
    """Load metric data from gzipped JSON files."""
    metric_path = Path(data_dir) / metric_name
    files = sorted(list(metric_path.glob("*.json.gz")))[:num_files]
    
    all_data = []
    for file_path in files:
        with gzip.open(file_path, 'rt') as f:
            data = json.load(f)
            if 'data' in data and 'result' in data['data']:
                for result in data['data']['result']:
                    if 'values' in result:
                        all_data.extend(result['values'])
    
    df = pd.DataFrame(all_data, columns=['timestamp', 'value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna()
    
    return df


def generate_summary_stats(metric_data_dict):
    """Generate summary statistics for all metrics."""
    summary = []
    for metric_name, df in metric_data_dict.items():
        stats_dict = {
            'Metric': metric_name,
            'N': len(df),
            'Mean': df['value'].mean(),
            'Median': df['value'].median(),
            'Std': df['value'].std(),
            'Min': df['value'].min(),
            'Max': df['value'].max(),
            'Q1': df['value'].quantile(0.25),
            'Q3': df['value'].quantile(0.75),
        }
        summary.append(stats_dict)
    
    return pd.DataFrame(summary)


def plot_correlation_matrix(metric_data_dict, output_dir):
    """Create correlation matrix heatmap."""
    dfs = []
    for metric_name, df in metric_data_dict.items():
        df_copy = df.copy()
        df_copy['time_key'] = df_copy['timestamp'].dt.round('1min')
        df_copy = df_copy.groupby('time_key')['value'].mean().reset_index()
        df_copy.columns = ['time_key', metric_name]
        dfs.append(df_copy)
    
    merged = dfs[0]
    for df in dfs[1:]:
        merged = pd.merge(merged, df, on='time_key', how='inner')
    
    if len(merged) < 10:
        print("Warning: Insufficient overlapping data for correlation matrix")
        return
    
    corr_matrix = merged.drop('time_key', axis=1).corr()
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                vmin=-1, vmax=1, fmt='.3f')
    plt.title('Metric Correlation Matrix', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'correlation_matrix.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Correlation matrix saved to: {output_path}")
    plt.close()
    
    return corr_matrix


def plot_overview(metric_data_dict, output_dir):
    """Create overview plots for all metrics."""
    n_metrics = len(metric_data_dict)
    fig, axes = plt.subplots(n_metrics, 2, figsize=(14, 4*n_metrics))
    
    if n_metrics == 1:
        axes = axes.reshape(1, -1)
    
    for idx, (metric_name, df) in enumerate(metric_data_dict.items()):
        ax_ts = axes[idx, 0]
        ax_ts.plot(df['timestamp'], df['value'], linewidth=0.6, alpha=0.7)
        ax_ts.set_ylabel(metric_name, fontweight='bold')
        ax_ts.set_title(f'{metric_name} Time Series', fontweight='bold')
        ax_ts.grid(True, alpha=0.3)
        
        ax_dist = axes[idx, 1]
        ax_dist.hist(df['value'], bins=40, alpha=0.7, color='steelblue', edgecolor='black')
        ax_dist.set_xlabel('Value', fontweight='bold')
        ax_dist.set_ylabel('Frequency', fontweight='bold')
        ax_dist.set_title(f'{metric_name} Distribution', fontweight='bold')
        ax_dist.grid(True, alpha=0.3, axis='y')
        
        mean_val = df['value'].mean()
        median_val = df['value'].median()
        ax_dist.axvline(mean_val, color='r', linestyle='--', linewidth=2, label=f'μ={mean_val:.2f}')
        ax_dist.axvline(median_val, color='g', linestyle='--', linewidth=2, label=f'median={median_val:.2f}')
        ax_dist.legend()
    
    axes[-1, 0].set_xlabel('Time', fontweight='bold')
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'eda_overview.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Overview plot saved to: {output_path}")
    plt.close()


def plot_load_efficiency(metric_data_dict, output_dir):
    """Plot node load efficiency vs power draw."""
    if 'node_load1' not in metric_data_dict or 'rPDULoadStatusLoad' not in metric_data_dict:
        print("Skipping efficiency plot (required metrics missing)")
        return

    df_load = metric_data_dict['node_load1'].copy()
    df_power = metric_data_dict['rPDULoadStatusLoad'].copy()

    # Downsampling first to avoid memory issues
    # Grouping by 1-minute intervals and take mean
    df_load['time_key'] = df_load['timestamp'].dt.round('1min')
    df_power['time_key'] = df_power['timestamp'].dt.round('1min')
    
    # Aggregating before merging to reduce data size
    df_load_agg = df_load.groupby('time_key')['value'].mean().reset_index()
    df_load_agg.columns = ['time_key', 'value_load']
    
    df_power_agg = df_power.groupby('time_key')['value'].mean().reset_index()
    df_power_agg.columns = ['time_key', 'value_power']

    # Now merging the aggregated data (much smaller)
    merged = pd.merge(df_load_agg, df_power_agg, on='time_key')

    merged['efficiency'] = merged['value_load'] / merged['value_power']
    merged = merged.replace([np.inf, -np.inf], np.nan).dropna()

    print(f"Merged {len(merged)} time points for efficiency analysis")

    plt.figure(figsize=(10, 5))
    sns.scatterplot(x='value_power', y='efficiency', data=merged, alpha=0.5)
    plt.title("Load Efficiency vs Power Draw", fontsize=14, fontweight='bold')
    plt.xlabel("rPDULoadStatusLoad (Power)")
    plt.ylabel("Load Efficiency (node_load1 / rPDULoadStatusLoad)")
    plt.grid(True, alpha=0.3)

    output_path = os.path.join(output_dir, 'load_efficiency.png')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Efficiency plot saved to: {output_path}")
    plt.close()

def detect_anomalies(df, metric_name):
    """Detect anomalies using IQR method."""
    Q1 = df['value'].quantile(0.25)
    Q3 = df['value'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 3 * IQR
    upper_bound = Q3 + 3 * IQR
    anomalies = df[(df['value'] < lower_bound) | (df['value'] > upper_bound)]
    return {
        'metric': metric_name,
        'n_anomalies': len(anomalies),
        'pct_anomalies': len(anomalies) / len(df) * 100,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
    }


def detect_anomalies_zscore(df, metric_name, threshold=3):
    """Detect anomalies using Z-score method."""
    z_scores = np.abs(stats.zscore(df['value'], nan_policy='omit'))
    anomalies = df[z_scores > threshold]
    return len(anomalies), (len(anomalies) / len(df) * 100)


def generate_report(metric_data_dict, output_dir):
    """Generate text report."""
    report_path = os.path.join(output_dir, 'eda_report.txt')
    with open(report_path, 'w') as f:
        f.write("EXPLORATORY DATA ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Number of metrics: {len(metric_data_dict)}\n\n")
        
        f.write("SUMMARY STATISTICS\n")
        summary_df = generate_summary_stats(metric_data_dict)
        f.write(summary_df.to_string(index=False))
        f.write("\n\n")

        f.write("ANOMALY DETECTION (3x IQR method)\n")
        for metric_name, df in metric_data_dict.items():
            anomaly_info = detect_anomalies(df, metric_name)
            f.write(f"\n{metric_name}:\n")
            f.write(f"  Anomalies: {anomaly_info['n_anomalies']} ({anomaly_info['pct_anomalies']:.2f}%)\n")
            f.write(f"  Bounds: [{anomaly_info['lower_bound']:.2f}, {anomaly_info['upper_bound']:.2f}]\n")

        f.write("\nANOMALY DETECTION (Z-score method)\n")
        for metric_name, df in metric_data_dict.items():
            n_ano, pct_ano = detect_anomalies_zscore(df, metric_name)
            f.write(f"{metric_name}: {n_ano} anomalies ({pct_ano:.2f}%)\n")

        for metric_name, df in metric_data_dict.items():
            cv = df['value'].std() / df['value'].mean() if df['value'].mean() != 0 else 0
            skewness = df['value'].skew()
            f.write(f"\n{metric_name}:\n")
            f.write(f"  - Coefficient of Variation: {cv:.3f} ")
            f.write("(high variability)\n" if cv > 0.5 else "(moderate variability)\n")
            f.write(f"  - Skewness: {skewness:.3f} ")
            if abs(skewness) < 0.5:
                f.write("(approximately symmetric)\n")
            elif skewness > 0:
                f.write("(right-skewed, occasional high values)\n")
            else:
                f.write("(left-skewed, occasional low values)\n")

    print(f"Text report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive EDA report')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--num-files', type=int, default=5, help='Number of files per metric')
    parser.add_argument('--output-dir', default='outputs/figs', help='Output directory')
    parser.add_argument('--metrics', nargs='+', 
                       default=['node_load1', 'node_procs_running', 'rPDULoadStatusLoad'],
                       help='Metrics to analyze')
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("EXPLORATORY DATA ANALYSIS")
    
    metric_data = {}
    for metric in args.metrics:
        try:
            print(f"Loading {metric}...")
            df = load_metric_data(metric, args.data_dir, args.num_files)
            n_files, start_time, end_time, span = get_data_span_info(metric, args.data_dir, args.num_files)
            metric_data[metric] = df
            print(f"{len(df)} data points loaded")
            if span:
                print(f"  • Files: {n_files}, Duration: {span[0]} days ({span[1]} hours)")
        except Exception as e:
            print(f"Error: {e}")
    
    if not metric_data:
        print("No data loaded. Exiting.")
        return
    
    print("Generating visualizations...")
    plot_overview(metric_data, args.output_dir)
    plot_correlation_matrix(metric_data, args.output_dir)
    plot_load_efficiency(metric_data, args.output_dir)
    
    print("Generating text report...")
    generate_report(metric_data, 'outputs/logs')

    print("EDA COMPLETE!")
    print(f"Outputs saved to: {args.output_dir}")
    print(f"  - eda_overview.png")
    print(f"  - correlation_matrix.png")
    print(f"  - load_efficiency.png")
    print(f"  - eda_report.txt")


if __name__ == '__main__':
    main()
