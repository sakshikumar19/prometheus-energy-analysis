# Run: python -m src.cli.run_pair_analysis --file1 data/disk_io.json.gz --file2 data/power.json.gz --window 30
# python -m src.cli.run_pair_analysis --file1 data/node_disk_io_time_seconds_total/1754002800.0.json.gz --file2 data/rPDULoadStatusLoad/1754002800.0.json.gz --window 30

import argparse
from src.load_prometheus import load_prometheus_file
from src.sync_metrics import align_metrics
from src.correlations import compute_correlations, lag_correlation, rate_correlation
from src.rolling_stats import rolling_corr
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

def plot_timeseries(df, out_path):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax2 = ax.twinx()
    ax.plot(df["datetime"], df["v1"], alpha=0.6, color="blue", label="v1", linewidth=0.5)
    ax2.plot(df["datetime"], df["v2"], alpha=0.6, color="red", label="v2", linewidth=0.5)
    
    ax.set_xlabel("Time")
    ax.set_ylabel("v1", color="blue")
    ax2.set_ylabel("v2", color="red")
    ax.tick_params(axis="y", labelcolor="blue")
    ax2.tick_params(axis="y", labelcolor="red")
    
    plt.title("Aligned Time Series")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_rolling_corr(df, out_path):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    valid = df["roll_corr"].notna()
    if valid.sum() > 0:
        ax.plot(df.loc[valid, "datetime"], df.loc[valid, "roll_corr"], linewidth=1)
        ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Time")
        ax.set_ylabel("Rolling Correlation")
        ax.set_title(f"Rolling Correlation (window={df['roll_corr'].notna().sum()} points)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
    plt.close()

def plot_scatter(df, out_path):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    sample_size = min(50000, len(df))
    if sample_size < len(df):
        sample_df = df.sample(n=sample_size, random_state=42)
    else:
        sample_df = df
    
    ax.scatter(sample_df["v1"], sample_df["v2"], alpha=0.1, s=1)
    ax.set_xlabel("v1")
    ax.set_ylabel("v2")
    ax.set_title("Scatter Plot")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_lag_analysis(lag_res, out_path):
    if not lag_res or lag_res["all_lags"].empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    lags_df = lag_res["all_lags"]
    ax.plot(lags_df["lag"], lags_df["corr"], marker="o", markersize=3, linewidth=1)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.axvline(x=0, color="gray", linestyle="--", alpha=0.5)
    
    best_lag = lag_res["best_lag"]
    best_corr = lag_res["best_corr"]
    ax.plot(best_lag, best_corr, marker="*", markersize=12, color="red", label=f"Best: lag={best_lag}, r={best_corr:.3f}")
    
    ax.set_xlabel("Lag (steps)")
    ax.set_ylabel("Correlation")
    ax.set_title("Lag Correlation Analysis")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file1", required=True)
    p.add_argument("--file2", required=True)
    p.add_argument("--window", type=int, default=30)
    p.add_argument("--outdir", default="results")
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print("Loading data")
    df1 = load_prometheus_file(args.file1)
    df2 = load_prometheus_file(args.file2)

    print(f"Loaded {len(df1)} points from file1, {len(df2)} points from file2")

    print("Aligning metrics")
    aligned = align_metrics(df1, df2)
    print(f"Aligned to {len(aligned)} points")

    if aligned.empty:
        print("No aligned data found")
        return

    corr = compute_correlations(aligned)
    corr_norm = compute_correlations(aligned, use_norm=True)
    
    print("Correlation summary (raw)")
    print(corr)
    print("\nCorrelation summary (normalized)")
    print(corr_norm)

    lag_res = lag_correlation(aligned, max_lag=20)
    if lag_res:
        print(f"Best lag correlation: lag={lag_res['best_lag']}, r={lag_res['best_corr']:.4f}, p={lag_res['best_p']:.4f}")

    rate_res = rate_correlation(aligned)
    if rate_res:
        print(f"Rate of change correlation: r={rate_res['corr']:.4f}, p={rate_res['p']:.4f}")

    print(f"\nComputing rolling correlation (window={args.window})...")
    rolling = rolling_corr(aligned, args.window)
    
    valid_corr = rolling["roll_corr"].notna().sum()
    if valid_corr > 0:
        roll_vals = rolling["roll_corr"].dropna()
        print(f"Rolling correlation computed for {valid_corr} points")
        print(f"Mean: {roll_vals.mean():.4f}, Std: {roll_vals.std():.4f}")
        print(f"Min: {roll_vals.min():.4f}, Max: {roll_vals.max():.4f}")
        print(f"Q25: {roll_vals.quantile(0.25):.4f}, Q75: {roll_vals.quantile(0.75):.4f}")

    out_path = os.path.join(args.outdir, "rolling_corr.csv")
    rolling.to_csv(out_path, index=False)
    print(f"Saved rolling correlation to: {out_path}")

    print("Generating visualizations")
    plot_timeseries(aligned, os.path.join(args.outdir, "timeseries.png"))
    plot_scatter(aligned, os.path.join(args.outdir, "scatter.png"))
    
    if lag_res:
        plot_lag_analysis(lag_res, os.path.join(args.outdir, "lag_analysis.png"))
    
    if valid_corr > 0:
        plot_rolling_corr(rolling, os.path.join(args.outdir, "rolling_corr.png"))

    print(f"Results saved to: {args.outdir}")

if __name__ == "__main__":
    main()
