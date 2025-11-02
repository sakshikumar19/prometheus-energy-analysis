# Run: python -m src.cli.run_pair_analysis --file1 data/disk_io.json.gz --file2 data/power.json.gz --window 30
# python -m src.cli.run_pair_analysis --file1 data/node_disk_io_time_seconds_total/1754002800.0.json.gz --file2 data/rPDULoadStatusLoad/1754002800.0.json.gz --window 30

import argparse
from src.load_prometheus import load_prometheus_file
from src.sync_metrics import align_metrics
from src.correlations import compute_correlations, lag_correlation, rate_correlation
from src.rolling_stats import rolling_corr
from src.visualization import plot_timeseries, plot_scatter, plot_lag_analysis, plot_rolling_corr
import os

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