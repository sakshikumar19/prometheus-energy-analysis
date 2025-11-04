from src.load_prometheus import load_prometheus_file
from src.sync_metrics import align_metrics, to_rate
from src.correlations import compute_correlations
from src.visualization import plot_12hr_scatter, plot_12hr_heatmap
import os
import pandas as pd
from datetime import datetime

def analyze_pair(machine_id, file1, file2, metric1_name="Disk IO", metric2_name="Power", outdir="results", hours=12, window_start=None, window_end=None):
    os.makedirs(outdir, exist_ok=True)

    df1 = load_prometheus_file(file1, machine=machine_id)
    df2 = load_prometheus_file(file2, machine=machine_id)
    if df1.empty or df2.empty:
        print(f"No data for machine: {machine_id}")
        return None

    df1 = to_rate(df1, metric1_name)
    df2 = to_rate(df2, metric2_name)

    aligned = align_metrics(df1, df2)
    if aligned.empty:
        print("No aligned data")
        return None

    aligned = aligned.sort_values("datetime").reset_index(drop=True)

    if window_start and window_end:
        if isinstance(window_start, str):
            window_start = datetime.fromisoformat(window_start.replace("Z", "+00:00")).replace(tzinfo=None)
        if isinstance(window_end, str):
            window_end = datetime.fromisoformat(window_end.replace("Z", "+00:00")).replace(tzinfo=None)
        windowed = aligned[(aligned["datetime"] >= window_start) & (aligned["datetime"] <= window_end)].copy()
        window_label = f"{window_start:%Y-%m-%dT%H-%M}_to_{window_end:%Y-%m-%dT%H-%M}"
    else:
        latest_time = aligned["datetime"].max()
        win_start = latest_time - pd.Timedelta(hours=hours)
        windowed = aligned[aligned["datetime"] >= win_start].copy()
        window_label = f"last_{hours}h"

    if len(windowed) < 10:
        print(f"Too few points in window: {len(windowed)}")
        return None

    corr = compute_correlations(windowed)

    machine_safe = machine_id.replace(".", "_").replace(":", "_").replace("/", "_")
    pair_safe = f"{metric1_name.replace(' ', '_')}_vs_{metric2_name.replace(' ', '_')}"
    run_dir = os.path.join(outdir, machine_safe, pair_safe, window_label)

    i = 0
    final_dir = run_dir
    while os.path.exists(final_dir):
        i += 1
        final_dir = f"{run_dir}_{i}"
    os.makedirs(final_dir, exist_ok=True)

    scatter_path = os.path.join(final_dir, "scatter.png")
    heatmap_path = os.path.join(final_dir, "heatmap.png")
    notes_path = os.path.join(final_dir, "notes.txt")

    plot_12hr_scatter(windowed, scatter_path, metric1_name, metric2_name)
    plot_12hr_heatmap(windowed, heatmap_path, metric1_name, metric2_name)

    with open(notes_path, "w") as f:
        f.write(f"Machine: {machine_id}\n")
        f.write(f"Metric 1: {metric1_name}\n")
        f.write(f"Metric 2: {metric2_name}\n")
        f.write(f"Window: {windowed['datetime'].min()} to {windowed['datetime'].max()}\n")
        if corr:
            f.write(f"Pearson r: {corr['pearson_r']:.4f} (p={corr['pearson_p']:.4f})\n")
            f.write(f"Spearman r: {corr['spearman_r']:.4f} (p={corr['spearman_p']:.4f})\n")
            f.write(f"N: {corr['n']}\n")

    print(f"Saved to {final_dir}")
    return {"dir": final_dir, "correlation": corr, "windowed_data": windowed}
