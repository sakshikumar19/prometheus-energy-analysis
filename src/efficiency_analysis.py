#!/usr/bin/env python3
"""
Analyze energy efficiency metrics (load vs power consumption).

Usage:
    python efficiency_analysis.py --load-metric node_load1 --power-metric rPDULoadStatusLoad --num-files 3
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


def align_and_compute_efficiency(df_load, df_power, load_name, power_name):
    """Align load and power metrics, compute efficiency."""
    # Downsampling to 1-minute intervals
    df_load_copy = df_load.copy()
    df_power_copy = df_power.copy()
    
    df_load_copy['time_key'] = df_load_copy['timestamp'].dt.round('1min')
    df_power_copy['time_key'] = df_power_copy['timestamp'].dt.round('1min')

    # Aggregating
    df_load_agg = df_load_copy.groupby('time_key')['value'].mean().reset_index()
    df_load_agg.columns = ['time_key', 'load']
    
    df_power_agg = df_power_copy.groupby('time_key')['value'].mean().reset_index()
    df_power_agg.columns = ['time_key', 'power']
    
    merged = pd.merge(df_load_agg, df_power_agg, on='time_key', how='inner')
    
    # Computing efficiency (load per unit power)
    merged['efficiency'] = merged['load'] / merged['power']
    
    merged = merged.replace([np.inf, -np.inf], np.nan).dropna()
    
    return merged


def categorize_load_states(merged, load_percentiles=[33, 67]):
    """Categorize data into load states (low, medium, high)."""
    p33, p67 = np.percentile(merged['load'], load_percentiles)
    
    conditions = [
        merged['load'] <= p33,
        (merged['load'] > p33) & (merged['load'] <= p67),
        merged['load'] > p67
    ]
    choices = ['Low Load', 'Medium Load', 'High Load']
    merged['load_state'] = np.select(conditions, choices, default='Unknown')
    
    return merged, {'p33': p33, 'p67': p67}


def calculate_efficiency_stats(merged):
    """Calculate efficiency statistics by load state."""
    stats_by_state = merged.groupby('load_state').agg({
        'efficiency': ['mean', 'std', 'median', 'min', 'max', 'count'],
        'load': ['mean', 'std'],
        'power': ['mean', 'std']
    }).round(4)
    
    return stats_by_state


def plot_efficiency_analysis(merged, output_dir, load_name, power_name, verbose=False):
    """Create comprehensive efficiency analysis plots."""
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # Efficiency vs Power (scatter)
    ax1 = fig.add_subplot(gs[0, 0])
    scatter = ax1.scatter(merged['power'], merged['efficiency'], 
                         c=merged['load'], cmap='viridis', alpha=0.5, s=10)
    ax1.set_xlabel(f'{power_name} (Power)', fontweight='bold')
    ax1.set_ylabel('Efficiency (Load/Power)', fontweight='bold')
    ax1.set_title('Efficiency vs Power Consumption', fontweight='bold', pad=10)
    ax1.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Load', fontweight='bold')
    
    # Efficiency vs Load (scatter)
    ax2 = fig.add_subplot(gs[0, 1])
    scatter2 = ax2.scatter(merged['load'], merged['efficiency'], 
                          c=merged['power'], cmap='plasma', alpha=0.5, s=10)
    ax2.set_xlabel(f'{load_name} (Load)', fontweight='bold')
    ax2.set_ylabel('Efficiency (Load/Power)', fontweight='bold')
    ax2.set_title('Efficiency vs System Load', fontweight='bold', pad=10)
    ax2.grid(True, alpha=0.3)
    cbar2 = plt.colorbar(scatter2, ax=ax2)
    cbar2.set_label('Power', fontweight='bold')
    
    # Efficiency by Load State (box plot)
    ax3 = fig.add_subplot(gs[1, 0])
    load_states_order = ['Low Load', 'Medium Load', 'High Load']
    sns.boxplot(data=merged, x='load_state', y='efficiency', order=load_states_order, ax=ax3)
    ax3.set_xlabel('Load State', fontweight='bold')
    ax3.set_ylabel('Efficiency', fontweight='bold')
    ax3.set_title('Efficiency Distribution by Load State', fontweight='bold', pad=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Power by Load State (box plot)
    ax4 = fig.add_subplot(gs[1, 1])
    sns.boxplot(data=merged, x='load_state', y='power', order=load_states_order, ax=ax4)
    ax4.set_xlabel('Load State', fontweight='bold')
    ax4.set_ylabel(f'{power_name} (Power)', fontweight='bold')
    ax4.set_title('Power Consumption by Load State', fontweight='bold', pad=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Time series of efficiency
    ax5 = fig.add_subplot(gs[2, :])
    ax5.plot(merged['time_key'], merged['efficiency'], linewidth=0.5, alpha=0.6, color='steelblue')
    
    if len(merged) > 100:
        window = max(10, len(merged) // 100)
        rolling_mean = merged['efficiency'].rolling(window=window, center=True).mean()
        ax5.plot(merged['time_key'], rolling_mean, linewidth=2, color='red', 
                alpha=0.8, label=f'Rolling Mean (window={window})')
    
    ax5.set_xlabel('Time', fontweight='bold')
    ax5.set_ylabel('Efficiency (Load/Power)', fontweight='bold')
    ax5.set_title('Efficiency Over Time', fontweight='bold', pad=10)
    ax5.grid(True, alpha=0.3)
    ax5.legend(loc='upper right')
    
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    output_path = os.path.join(output_dir, 'efficiency_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Efficiency analysis plot saved to: {output_path}")
    plt.close()


def plot_power_efficiency_heatmap(merged, output_dir, verbose=False):
    """Create 2D histogram heatmap of load vs power colored by efficiency."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    load_bins = np.linspace(merged['load'].min(), merged['load'].max(), 30)
    power_bins = np.linspace(merged['power'].min(), merged['power'].max(), 30)
    
    # Assigning each point to a bin and calculating mean efficiency per bin
    merged['load_bin'] = pd.cut(merged['load'], bins=load_bins)
    merged['power_bin'] = pd.cut(merged['power'], bins=power_bins)
    
    heatmap_data = merged.groupby(['load_bin', 'power_bin'])['efficiency'].mean().unstack()
    
    sns.heatmap(heatmap_data, cmap='RdYlGn', cbar_kws={'label': 'Mean Efficiency'}, ax=ax)
    ax.set_xlabel('Power Bin', fontweight='bold')
    ax.set_ylabel('Load Bin', fontweight='bold')
    ax.set_title('Efficiency Heatmap (Load vs Power)', fontweight='bold', pad=10)
    
    output_path = os.path.join(output_dir, 'efficiency_heatmap.png')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Efficiency heatmap saved to: {output_path}")
    plt.close()


def generate_efficiency_report(merged, stats_by_state, load_name, power_name, 
                               output_dir, percentiles, verbose=False):
    """Generate comprehensive efficiency report."""
    report_path = os.path.join(output_dir, 'efficiency_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("ENERGY EFFICIENCY ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Load Metric: {load_name}\n")
        f.write(f"Power Metric: {power_name}\n")
        f.write(f"Total data points: {len(merged)}\n\n")
        
        f.write("EFFICIENCY DEFINITION\n")
        f.write(f"Efficiency = {load_name} / {power_name}\n")
        f.write("Higher efficiency indicates more computational load per unit of power.\n\n")
        
        f.write("LOAD STATE THRESHOLDS\n")
        f.write(f"Low Load:    load <= {percentiles['p33']:.2f}\n")
        f.write(f"Medium Load: {percentiles['p33']:.2f} < load <= {percentiles['p67']:.2f}\n")
        f.write(f"High Load:   load > {percentiles['p67']:.2f}\n\n")
        
        f.write("OVERALL EFFICIENCY STATISTICS\n")
        f.write(f"Mean Efficiency: {merged['efficiency'].mean():.4f}\n")
        f.write(f"Median Efficiency: {merged['efficiency'].median():.4f}\n")
        f.write(f"Std Dev: {merged['efficiency'].std():.4f}\n")
        f.write(f"Min: {merged['efficiency'].min():.4f}\n")
        f.write(f"Max: {merged['efficiency'].max():.4f}\n")
        f.write(f"25th percentile: {merged['efficiency'].quantile(0.25):.4f}\n")
        f.write(f"75th percentile: {merged['efficiency'].quantile(0.75):.4f}\n\n")
        
        f.write("EFFICIENCY BY LOAD STATE\n")
        f.write(stats_by_state.to_string())
        f.write("\n\n")
        
        f.write("KEY INSIGHTS\n")
        
        corr = merged[['load', 'power', 'efficiency']].corr()
        f.write(f"Correlation (Load vs Power): {corr.loc['load', 'power']:.4f}\n")
        f.write(f"Correlation (Load vs Efficiency): {corr.loc['load', 'efficiency']:.4f}\n")
        f.write(f"Correlation (Power vs Efficiency): {corr.loc['power', 'efficiency']:.4f}\n\n")
        
        state_means = merged.groupby('load_state')['efficiency'].mean()
        f.write("Mean Efficiency by State:\n")
        for state in ['Low Load', 'Medium Load', 'High Load']:
            if state in state_means.index:
                f.write(f"  {state}: {state_means[state]:.4f}\n")
        
        f.write("\nOptimal Operating Range:\n")
        high_eff_threshold = merged['efficiency'].quantile(0.75)
        optimal_data = merged[merged['efficiency'] >= high_eff_threshold]
        f.write(f"  Top 25% efficiency threshold: {high_eff_threshold:.4f}\n")
        f.write(f"  Optimal load range: [{optimal_data['load'].min():.2f}, {optimal_data['load'].max():.2f}]\n")
        f.write(f"  Optimal power range: [{optimal_data['power'].min():.2f}, {optimal_data['power'].max():.2f}]\n")
        
    
    if verbose:
        print(f"Efficiency report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze energy efficiency metrics')
    parser.add_argument('--load-metric', default='node_load1',
                        help='Load metric name (default: node_load1)')
    parser.add_argument('--power-metric', default='rPDULoadStatusLoad',
                        help='Power metric name (default: rPDULoadStatusLoad)')
    parser.add_argument('--data-dir', default='data',
                        help='Data directory (default: data/)')
    parser.add_argument('--num-files', type=int, default=5,
                        help='Number of files per metric (default: 3)')
    parser.add_argument('--output-dir', default='outputs/figs',
                        help='Output directory (default: outputs/figs/)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.join('outputs', 'logs'), exist_ok=True)  # ensure logs directory exists
    
    print("ENERGY EFFICIENCY ANALYSIS")
    
    print(f"Loading {args.load_metric}...")
    df_load = load_metric_data(args.load_metric, args.data_dir, args.num_files)
    print(f"{len(df_load)} data points loaded")
    
    print(f"Loading {args.power_metric}...")
    df_power = load_metric_data(args.power_metric, args.data_dir, args.num_files)
    print(f"{len(df_power)} data points loaded")
    
    print("\nAligning metrics and computing efficiency...")
    merged = align_and_compute_efficiency(df_load, df_power, args.load_metric, args.power_metric)
    print(f"{len(merged)} aligned data points")
    
    if len(merged) < 10:
        print("Insufficient data for efficiency analysis")
        return
    
    print("Categorizing load states...")
    merged, percentiles = categorize_load_states(merged)
    print(f"Low: <={percentiles['p33']:.2f}, Medium: {percentiles['p33']:.2f}-{percentiles['p67']:.2f}, High: >{percentiles['p67']:.2f}")
    
    print("Calculating efficiency statistics...")
    stats_by_state = calculate_efficiency_stats(merged)
    print(f"Statistics computed for {len(stats_by_state)} load states")
    
    print("\nGenerating efficiency plots...")
    plot_efficiency_analysis(merged, args.output_dir, args.load_metric, args.power_metric, args.verbose)
    
    print("Generating efficiency heatmap...")
    plot_power_efficiency_heatmap(merged, args.output_dir, args.verbose)
    
    print("Generating efficiency report...")
    generate_efficiency_report(merged, stats_by_state, args.load_metric, args.power_metric, 
                              os.path.join('outputs', 'logs'), percentiles, args.verbose)
    
    print("ANALYSIS COMPLETE!")
    print(f"Plots saved to: {args.output_dir}")
    print(f"Report saved to: {os.path.join('outputs', 'logs', 'efficiency_report.txt')}")

if __name__ == '__main__':
    main()