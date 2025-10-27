#!/usr/bin/env python3
"""
Generate visualizations for metric analysis.

Usage:
    python visualization.py --metric1 node_load1 --metric2 rPDULoadStatusLoad --num-files 3
    python visualization.py --metric node_load1 --window 12 --single
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
from datetime import datetime, timedelta


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


def filter_time_window(df, window_hours=12):
    """Filter data to specified time window."""
    if len(df) == 0:
        return df
    
    end_time = df['timestamp'].max()
    start_time = end_time - timedelta(hours=window_hours)
    return df[df['timestamp'] >= start_time].copy()


def create_heatmap_data(df, metric_name, bin_minutes=15):
    """Create binned heatmap data from time series."""
    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    df['minute_bin'] = (df['timestamp'].dt.minute // bin_minutes) * bin_minutes
    
    heatmap = df.groupby(['hour', 'minute_bin'])['value'].mean().reset_index()
    pivot = heatmap.pivot(index='minute_bin', columns='hour', values='value')
    
    return pivot


def plot_dual_heatmap(df1, df2, metric1_name, metric2_name, output_path, window_hours):
    """Create dual heatmap visualization."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    hm1 = create_heatmap_data(df1, metric1_name)
    hm2 = create_heatmap_data(df2, metric2_name)
    
    sns.heatmap(hm1, ax=axes[0], cmap='YlOrRd', cbar_kws={'label': 'Value'})
    axes[0].set_title(f'{metric1_name} - {window_hours}hr Window Heatmap', fontweight='bold', pad=10)
    axes[0].set_xlabel('Hour of Day', fontweight='bold')
    axes[0].set_ylabel('Minute (binned)', fontweight='bold')
    
    sns.heatmap(hm2, ax=axes[1], cmap='YlGnBu', cbar_kws={'label': 'Value'})
    axes[1].set_title(f'{metric2_name} - {window_hours}hr Window Heatmap', fontweight='bold', pad=10)
    axes[1].set_xlabel('Hour of Day', fontweight='bold')
    axes[1].set_ylabel('Minute (binned)', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Dual heatmap saved to: {output_path}")
    plt.close()


def plot_scatter_grid(df1, df2, metric1_name, metric2_name, output_path):
    """Create scatter plot with marginal distributions."""
    df1_binned = df1.copy()
    df2_binned = df2.copy()
    
    df1_binned['time_key'] = df1_binned['timestamp'].dt.round('5min')
    df2_binned['time_key'] = df2_binned['timestamp'].dt.round('5min')
    
    df1_agg = df1_binned.groupby('time_key')['value'].mean().reset_index()
    df1_agg.columns = ['time_key', metric1_name]
    
    df2_agg = df2_binned.groupby('time_key')['value'].mean().reset_index()
    df2_agg.columns = ['time_key', metric2_name]
    
    merged = pd.merge(df1_agg, df2_agg, on='time_key', how='inner')
    
    if len(merged) < 2:
        print("Warning: Insufficient overlapping data for scatter plot")
        return
    
    fig = plt.figure(figsize=(10, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.05, wspace=0.05)
    
    ax_main = fig.add_subplot(gs[1:, :-1])
    ax_top = fig.add_subplot(gs[0, :-1], sharex=ax_main)
    ax_right = fig.add_subplot(gs[1:, -1], sharey=ax_main)
    
    ax_main.scatter(merged[metric1_name], merged[metric2_name], 
                   alpha=0.6, s=20, c=range(len(merged)), cmap='viridis')
    ax_main.set_xlabel(metric1_name, fontweight='bold')
    ax_main.set_ylabel(metric2_name, fontweight='bold')
    ax_main.grid(True, alpha=0.3)
    
    ax_top.hist(merged[metric1_name], bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    ax_top.tick_params(labelbottom=False)
    ax_top.set_ylabel('Count', fontsize=9)
    
    ax_right.hist(merged[metric2_name], bins=30, color='coral', alpha=0.7, 
                 edgecolor='black', orientation='horizontal')
    ax_right.tick_params(labelleft=False)
    ax_right.set_xlabel('Count', fontsize=9)
    
    plt.suptitle(f'{metric1_name} vs {metric2_name} - Scatter with Distributions', 
                fontweight='bold', y=0.995)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Scatter grid saved to: {output_path}")
    plt.close()


def plot_time_series_comparison(df1, df2, metric1_name, metric2_name, output_path, window_hours):
    """Create detailed time series comparison."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    axes[0].plot(df1['timestamp'], df1['value'], linewidth=0.8, color='steelblue', alpha=0.8)
    axes[0].fill_between(df1['timestamp'], df1['value'], alpha=0.3, color='steelblue')
    axes[0].set_ylabel(metric1_name, fontweight='bold')
    axes[0].set_title(f'Time Series Comparison - {window_hours}hr Window', fontweight='bold', pad=10)
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(df2['timestamp'], df2['value'], linewidth=0.8, color='coral', alpha=0.8)
    axes[1].fill_between(df2['timestamp'], df2['value'], alpha=0.3, color='coral')
    axes[1].set_ylabel(metric2_name, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    df1_norm = (df1['value'] - df1['value'].min()) / (df1['value'].max() - df1['value'].min())
    df2_norm = (df2['value'] - df2['value'].min()) / (df2['value'].max() - df2['value'].min())
    
    axes[2].plot(df1['timestamp'], df1_norm, linewidth=1, color='steelblue', 
                alpha=0.8, label=metric1_name)
    axes[2].plot(df2['timestamp'], df2_norm, linewidth=1, color='coral', 
                alpha=0.8, label=metric2_name)
    axes[2].set_ylabel('Normalized Value', fontweight='bold')
    axes[2].set_xlabel('Time', fontweight='bold')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    
    plt.setp(axes[2].xaxis.get_majorticklabels(), rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Time series comparison saved to: {output_path}")
    plt.close()


def plot_rolling_statistics(df1, df2, metric1_name, metric2_name, output_path, window_size=20):
    """Plot rolling mean and standard deviation."""
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    
    df1_copy['rolling_mean'] = df1_copy['value'].rolling(window=window_size, center=True).mean()
    df1_copy['rolling_std'] = df1_copy['value'].rolling(window=window_size, center=True).std()
    
    df2_copy['rolling_mean'] = df2_copy['value'].rolling(window=window_size, center=True).mean()
    df2_copy['rolling_std'] = df2_copy['value'].rolling(window=window_size, center=True).std()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    axes[0, 0].plot(df1_copy['timestamp'], df1_copy['value'], 
                   alpha=0.3, linewidth=0.5, color='steelblue')
    axes[0, 0].plot(df1_copy['timestamp'], df1_copy['rolling_mean'], 
                   linewidth=2, color='darkblue', label='Rolling Mean')
    axes[0, 0].set_ylabel(metric1_name, fontweight='bold')
    axes[0, 0].set_title(f'{metric1_name} - Rolling Statistics', fontweight='bold', pad=10)
    axes[0, 0].legend(loc='upper right')
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].plot(df1_copy['timestamp'], df1_copy['rolling_std'], 
                   linewidth=1.5, color='darkred')
    axes[0, 1].fill_between(df1_copy['timestamp'], df1_copy['rolling_std'], 
                           alpha=0.3, color='darkred')
    axes[0, 1].set_ylabel('Rolling Std Dev', fontweight='bold')
    axes[0, 1].set_title(f'{metric1_name} - Variability', fontweight='bold', pad=10)
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].plot(df2_copy['timestamp'], df2_copy['value'], 
                   alpha=0.3, linewidth=0.5, color='coral')
    axes[1, 0].plot(df2_copy['timestamp'], df2_copy['rolling_mean'], 
                   linewidth=2, color='darkred', label='Rolling Mean')
    axes[1, 0].set_ylabel(metric2_name, fontweight='bold')
    axes[1, 0].set_title(f'{metric2_name} - Rolling Statistics', fontweight='bold', pad=10)
    axes[1, 0].legend(loc='upper right')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_xlabel('Time', fontweight='bold')
    
    axes[1, 1].plot(df2_copy['timestamp'], df2_copy['rolling_std'], 
                   linewidth=1.5, color='darkgreen')
    axes[1, 1].fill_between(df2_copy['timestamp'], df2_copy['rolling_std'], 
                           alpha=0.3, color='darkgreen')
    axes[1, 1].set_ylabel('Rolling Std Dev', fontweight='bold')
    axes[1, 1].set_title(f'{metric2_name} - Variability', fontweight='bold', pad=10)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlabel('Time', fontweight='bold')
    
    for ax in axes.flat:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Rolling statistics plot saved to: {output_path}")
    plt.close()


def plot_single_metric_overview(df, metric_name, output_path, window_hours):
    """Create comprehensive single metric visualization."""
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['timestamp'], df['value'], linewidth=0.8, color='steelblue')
    ax1.fill_between(df['timestamp'], df['value'], alpha=0.3, color='steelblue')
    ax1.set_ylabel('Value', fontweight='bold')
    ax1.set_title(f'{metric_name} - {window_hours}hr Overview', fontweight='bold', pad=10)
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax2 = fig.add_subplot(gs[1, 0])
    heatmap_data = create_heatmap_data(df, metric_name)
    sns.heatmap(heatmap_data, ax=ax2, cmap='YlOrRd', cbar_kws={'label': 'Value'})
    ax2.set_title('Hourly Pattern Heatmap', fontweight='bold', pad=10)
    ax2.set_xlabel('Hour', fontweight='bold')
    ax2.set_ylabel('Minute Bin', fontweight='bold')
    
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.hist(df['value'], bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Value', fontweight='bold')
    ax3.set_ylabel('Frequency', fontweight='bold')
    ax3.set_title('Distribution', fontweight='bold', pad=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    ax4 = fig.add_subplot(gs[2, 0])
    df_hourly = df.copy()
    df_hourly['hour'] = df_hourly['timestamp'].dt.hour
    hourly_mean = df_hourly.groupby('hour')['value'].mean()
    ax4.bar(hourly_mean.index, hourly_mean.values, color='coral', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Hour of Day', fontweight='bold')
    ax4.set_ylabel('Mean Value', fontweight='bold')
    ax4.set_title('Average by Hour', fontweight='bold', pad=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    ax5 = fig.add_subplot(gs[2, 1])
    rolling_mean = df['value'].rolling(window=20, center=True).mean()
    rolling_std = df['value'].rolling(window=20, center=True).std()
    ax5.plot(df['timestamp'], rolling_mean, linewidth=2, color='darkblue', label='Mean')
    ax5.plot(df['timestamp'], rolling_std, linewidth=2, color='darkred', label='Std Dev')
    ax5.set_xlabel('Time', fontweight='bold')
    ax5.set_ylabel('Value', fontweight='bold')
    ax5.set_title('Rolling Statistics', fontweight='bold', pad=10)
    ax5.legend(loc='upper right')
    ax5.grid(True, alpha=0.3)
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Single metric overview saved to: {output_path}")
    plt.close()


def generate_summary_report(df1, df2, metric1_name, metric2_name, window_hours, output_dir):
    """Generate summary statistics report."""
    report_path = os.path.join(output_dir, 'visualization_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("VISUALIZATION SUMMARY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Time Window: {window_hours} hours\n\n")
        
        f.write(f"Metric: {metric1_name}\n")
        f.write(f"  Data points: {len(df1)}\n")
        f.write(f"  Mean: {df1['value'].mean():.4f}\n")
        f.write(f"  Std Dev: {df1['value'].std():.4f}\n")
        f.write(f"  Min: {df1['value'].min():.4f}\n")
        f.write(f"  Max: {df1['value'].max():.4f}\n")
        f.write(f"  Median: {df1['value'].median():.4f}\n\n")
        
        if df2 is not None:
            f.write(f"Metric: {metric2_name}\n")
            f.write(f"  Data points: {len(df2)}\n")
            f.write(f"  Mean: {df2['value'].mean():.4f}\n")
            f.write(f"  Std Dev: {df2['value'].std():.4f}\n")
            f.write(f"  Min: {df2['value'].min():.4f}\n")
            f.write(f"  Max: {df2['value'].max():.4f}\n")
            f.write(f"  Median: {df2['value'].median():.4f}\n")
    
    print(f"Summary report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate metric visualizations')
    parser.add_argument('--metric1', '--metric', dest='metric1', default='node_load1',
                       help='First metric name')
    parser.add_argument('--metric2', default=None, help='Second metric name (optional)')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--num-files', type=int, default=5, help='Number of files per metric')
    parser.add_argument('--window', type=int, default=12, help='Time window in hours')
    parser.add_argument('--output-dir', default='outputs/figs', help='Output directory')
    parser.add_argument('--single', action='store_true', 
                       help='Single metric mode (only use metric1)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs('outputs/logs', exist_ok=True)
    
    print("METRIC VISUALIZATION")
    
    print(f"Loading {args.metric1}...")
    df1 = load_metric_data(args.metric1, args.data_dir, args.num_files)
    print(f"{len(df1)} data points loaded")
    
    df1 = filter_time_window(df1, args.window)
    print(f"{len(df1)} points in {args.window}hr window")
    
    if len(df1) == 0:
        print("Error: No data in time window")
        return
    
    if args.single or args.metric2 is None:
        print("\nGenerating single metric overview...")
        output_path = os.path.join(args.output_dir, f'{args.metric1}_overview.png')
        plot_single_metric_overview(df1, args.metric1, output_path, args.window)
        
        print("Generating summary report...")
        generate_summary_report(df1, None, args.metric1, None, args.window, 'outputs/logs')
        
        print("\nAnalysis complete!")
        print(f"Visualization saved to: {output_path}")
        return
    
    print(f"\nLoading {args.metric2}...")
    df2 = load_metric_data(args.metric2, args.data_dir, args.num_files)
    print(f"{len(df2)} data points loaded")
    
    df2 = filter_time_window(df2, args.window)
    print(f"{len(df2)} points in {args.window}hr window")
    
    if len(df2) == 0:
        print("Error: No data for metric2 in time window")
        return
    
    print("\nGenerating dual heatmap...")
    heatmap_path = os.path.join(args.output_dir, 
                               f'{args.metric1}_{args.metric2}_heatmap.png')
    plot_dual_heatmap(df1, df2, args.metric1, args.metric2, heatmap_path, args.window)
    
    print("Generating scatter plot with distributions...")
    scatter_path = os.path.join(args.output_dir, 
                               f'{args.metric1}_{args.metric2}_scatter.png')
    plot_scatter_grid(df1, df2, args.metric1, args.metric2, scatter_path)
    
    print("Generating time series comparison...")
    timeseries_path = os.path.join(args.output_dir, 
                                  f'{args.metric1}_{args.metric2}_timeseries.png')
    plot_time_series_comparison(df1, df2, args.metric1, args.metric2, 
                                timeseries_path, args.window)
    
    print("Generating rolling statistics...")
    rolling_path = os.path.join(args.output_dir, 
                               f'{args.metric1}_{args.metric2}_rolling.png')
    plot_rolling_statistics(df1, df2, args.metric1, args.metric2, rolling_path)
    
    print("Generating summary report...")
    generate_summary_report(df1, df2, args.metric1, args.metric2, args.window, 'outputs/logs')
    
    print("\nAnalysis complete!")
    print(f"Plots saved to: {args.output_dir}")
    print(f"Report saved to: outputs/logs/visualization_report.txt")


if __name__ == '__main__':
    main()