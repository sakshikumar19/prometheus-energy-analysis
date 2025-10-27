#!/usr/bin/env python3
"""
Analyze correlation between two metrics.

Usage:
    python analyze_pair.py --metric1 node_load1 --metric2 rPDULoadStatusLoad --num-files 3
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
from scipy import stats
from datetime import datetime

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


def align_metrics(df1, df2, metric1_name, metric2_name):
    """Align two metric dataframes by timestamp."""
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    
    df1_copy['time_key'] = df1_copy['timestamp'].dt.round('1min')
    df2_copy['time_key'] = df2_copy['timestamp'].dt.round('1min')
    
    df1_agg = df1_copy.groupby('time_key')['value'].mean().reset_index()
    df1_agg.columns = ['time_key', metric1_name]
    
    df2_agg = df2_copy.groupby('time_key')['value'].mean().reset_index()
    df2_agg.columns = ['time_key', metric2_name]
    
    merged = pd.merge(df1_agg, df2_agg, on='time_key', how='inner')
    
    return merged


def calculate_correlation_stats(merged, metric1_name, metric2_name):
    """Calculate correlation statistics."""
    pearson_corr, pearson_p = stats.pearsonr(merged[metric1_name], merged[metric2_name])
    spearman_corr, spearman_p = stats.spearmanr(merged[metric1_name], merged[metric2_name])
    
    return {
        'pearson_r': pearson_corr,
        'pearson_p': pearson_p,
        'spearman_r': spearman_corr,
        'spearman_p': spearman_p,
        'n_samples': len(merged)
    }


def plot_correlation(merged, metric1_name, metric2_name, output_path, stats_dict, verbose=False):
    """Create correlation visualization."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Scatter plot with regression line
    ax1 = axes[0]
    ax1.scatter(merged[metric1_name], merged[metric2_name], alpha=0.5, s=10)
    
    # Adding regression line
    z = np.polyfit(merged[metric1_name], merged[metric2_name], 1)
    p = np.poly1d(z)
    x_line = np.linspace(merged[metric1_name].min(), merged[metric1_name].max(), 100)
    ax1.plot(x_line, p(x_line), "r--", linewidth=2, label=f'y={z[0]:.3f}x+{z[1]:.3f}')
    
    ax1.set_xlabel(metric1_name, fontweight='bold')
    ax1.set_ylabel(metric2_name, fontweight='bold')
    ax1.set_title(f'Correlation: {metric1_name} vs {metric2_name}', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Adding correlation stats as text
    textstr = f"Pearson r = {stats_dict['pearson_r']:.3f} (p={stats_dict['pearson_p']:.2e})\n"
    textstr += f"Spearman ρ = {stats_dict['spearman_r']:.3f} (p={stats_dict['spearman_p']:.2e})\n"
    textstr += f"N = {stats_dict['n_samples']}"
    ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=9,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Time series overlay
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    
    line1 = ax2.plot(merged['time_key'], merged[metric1_name], 'b-', alpha=0.7, linewidth=1, label=metric1_name)
    line2 = ax2_twin.plot(merged['time_key'], merged[metric2_name], 'r-', alpha=0.7, linewidth=1, label=metric2_name)
    
    ax2.set_xlabel('Time', fontweight='bold')
    ax2.set_ylabel(metric1_name, fontweight='bold', color='b')
    ax2_twin.set_ylabel(metric2_name, fontweight='bold', color='r')
    ax2.set_title('Time Series Overlay', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2_twin.tick_params(axis='y', labelcolor='r')
    ax2.grid(True, alpha=0.3)
    
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Correlation plot saved to: {output_path}")
    plt.close()


def generate_text_report(metric1_name, metric2_name, stats_dict, output_dir, verbose=False):
    """Generate text report for correlation analysis."""
    report_path = os.path.join(output_dir, 'correlation_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("CORRELATION ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Metric 1: {metric1_name}\n")
        f.write(f"Metric 2: {metric2_name}\n")
        f.write(f"Samples analyzed: {stats_dict['n_samples']}\n\n")
        
        f.write("CORRELATION COEFFICIENTS\n")
        f.write(f"Pearson correlation: r = {stats_dict['pearson_r']:.4f}\n")
        f.write(f"  p-value: {stats_dict['pearson_p']:.2e}\n")
        f.write(f"Spearman correlation: p = {stats_dict['spearman_r']:.4f}\n")
        f.write(f"  p-value: {stats_dict['spearman_p']:.2e}\n")
        
        abs_r = abs(stats_dict['pearson_r'])
        if abs_r >= 0.7:
            strength = "Strong"
        elif abs_r >= 0.4:
            strength = "Moderate"
        elif abs_r >= 0.2:
            strength = "Weak"
        else:
            strength = "Very weak or no"
        direction = "positive" if stats_dict['pearson_r'] > 0 else "negative"
        
        f.write("\nINTERPRETATION\n")
        f.write(f"{strength} {direction} correlation\n")
    
    if verbose:
        print(f"Text report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze correlation between two metrics')
    parser.add_argument('--metric1', default='node_load1', help='First metric name (default: node_load1)')
    parser.add_argument('--metric2', default='rPDULoadStatusLoad', help='Second metric name (default: rPDULoadStatusLoad)')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--num-files', type=int, default=5, help='Number of files per metric')
    parser.add_argument('--output', default='outputs/figs/correlation.png', help='Output plot path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    print("CORRELATION ANALYSIS")
    
    print(f"Loading {args.metric1}...")
    df1 = load_metric_data(args.metric1, args.data_dir, args.num_files)
    print(f"{len(df1)} data points loaded")
    
    print(f"Loading {args.metric2}...")
    df2 = load_metric_data(args.metric2, args.data_dir, args.num_files)
    print(f"{len(df2)} data points loaded")
    
    print("\nAligning metrics by timestamp...")
    merged = align_metrics(df1, df2, args.metric1, args.metric2)
    print(f"{len(merged)} aligned data points")
    
    if len(merged) < 10:
        print("  ✗ Insufficient overlapping data for correlation analysis")
        return
    
    print("\nCalculating correlation statistics...")
    stats_dict = calculate_correlation_stats(merged, args.metric1, args.metric2)
    print(f"Pearson r = {stats_dict['pearson_r']:.4f} (p={stats_dict['pearson_p']:.2e})")
    print(f"Spearman ρ = {stats_dict['spearman_r']:.4f} (p={stats_dict['spearman_p']:.2e})")
    
    print("\nGenerating correlation plot...")
    plot_correlation(merged, args.metric1, args.metric2, args.output, stats_dict, args.verbose)
    
    print("Generating text report...")
    generate_text_report(args.metric1, args.metric2, stats_dict, 'outputs/logs', args.verbose)
    
    print("ANALYSIS COMPLETE!")
    print(f"Output saved to: {args.output}")
    print(f"Report saved to: {os.path.join('outputs', 'logs', 'correlation_report.txt')}")

if __name__ == '__main__':
    main()