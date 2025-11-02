from src.load_prometheus import load_prometheus_file
from src.sync_metrics import align_metrics
from src.correlations import compute_correlations
from src.visualization import plot_12hr_scatter, plot_12hr_heatmap
import os
import pandas as pd

def analyze_pair(machine_id, file1, file2, metric1_name="Disk IO", metric2_name="Power", outdir="results", hours=12):
    os.makedirs(outdir, exist_ok=True)
    
    print(f"Analyzing {metric1_name} vs {metric2_name} for machine: {machine_id}")
    
    df1 = load_prometheus_file(file1, machine=machine_id)
    df2 = load_prometheus_file(file2, machine=machine_id)
    
    if df1.empty or df2.empty:
        print(f"Warning: No data found for machine '{machine_id}'")
        return None
    
    print(f"Loaded {len(df1)} points from {metric1_name}, {len(df2)} points from {metric2_name}")
    
    aligned = align_metrics(df1, df2)
    
    if aligned.empty:
        print("No aligned data found")
        return None
    
    print(f"Aligned to {len(aligned)} points")
    
    if len(aligned) == 0:
        return None
    
    aligned = aligned.sort_values("datetime").reset_index(drop=True)
    
    latest_time = aligned["datetime"].max()
    window_start = latest_time - pd.Timedelta(hours=hours)
    
    windowed = aligned[aligned["datetime"] >= window_start].copy()
    
    if len(windowed) < 10:
        print(f"Warning: Only {len(windowed)} points in {hours}-hour window")
        windowed = aligned.copy()
    
    print(f"Using {len(windowed)} points from {hours}-hour window")
    
    corr = compute_correlations(windowed)
    
    machine_safe = machine_id.replace(".", "_").replace(":", "_").replace("/", "_")
    base_name = f"{machine_safe}_{metric1_name.replace(' ', '_')}_vs_{metric2_name.replace(' ', '_')}"
    
    scatter_path = os.path.join(outdir, f"{base_name}_scatter.png")
    heatmap_path = os.path.join(outdir, f"{base_name}_heatmap.png")
    notes_path = os.path.join(outdir, f"{base_name}_notes.txt")
    
    plot_12hr_scatter(windowed, scatter_path, metric1_name, metric2_name)
    plot_12hr_heatmap(windowed, heatmap_path, metric1_name, metric2_name)
    
    with open(notes_path, "w") as f:
        f.write(f"Analysis: {metric1_name} vs {metric2_name}\n")
        f.write(f"Machine: {machine_id}\n")
        f.write(f"Time Window: {hours} hours ({windowed['datetime'].min()} to {windowed['datetime'].max()})\n")
        f.write(f"Data Points: {len(windowed)}\n\n")
        
        if corr:
            f.write(f"Correlation Summary:\n")
            f.write(f"  Pearson r: {corr['pearson_r']:.4f} (p={corr['pearson_p']:.4f})\n")
            f.write(f"  Spearman r: {corr['spearman_r']:.4f} (p={corr['spearman_p']:.4f})\n")
            f.write(f"  Sample size: {corr['n']}\n\n")
            
            if abs(corr['pearson_r']) > 0.5:
                direction = "positive" if corr['pearson_r'] > 0 else "negative"
                f.write(f"Observed Relationship:\n")
                f.write(f"  Strong {direction} correlation ({corr['pearson_r']:.3f}) between {metric1_name} and {metric2_name}.\n")
                if corr['pearson_r'] > 0:
                    f.write(f"  As {metric1_name} increases, {metric2_name} tends to increase.\n")
                else:
                    f.write(f"  As {metric1_name} increases, {metric2_name} tends to decrease.\n")
            elif abs(corr['pearson_r']) > 0.3:
                direction = "positive" if corr['pearson_r'] > 0 else "negative"
                f.write(f"Observed Relationship:\n")
                f.write(f"  Moderate {direction} correlation ({corr['pearson_r']:.3f}) between {metric1_name} and {metric2_name}.\n")
            else:
                f.write(f"Observed Relationship:\n")
                f.write(f"  Weak correlation ({corr['pearson_r']:.3f}) - no strong relationship observed in this {hours}-hour window.\n")
    
    print(f"Saved visualizations and notes to {outdir}")
    print(f"  - Scatter: {scatter_path}")
    print(f"  - Heatmap: {heatmap_path}")
    print(f"  - Notes: {notes_path}")
    
    return {
        "machine": machine_id,
        "correlation": corr,
        "windowed_data": windowed
    }
