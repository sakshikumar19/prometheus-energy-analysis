import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def _needs_log(s):
    clean = s.dropna()
    return len(clean) > 0 and clean.min() > 0 and clean.max() / clean.min() > 100

def plot_12hr_scatter(df, out_path, metric1_name="metric1", metric2_name="metric2"):
    if df.empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    xlabel = metric1_name
    ylabel = metric2_name
    if _needs_log(df["v1"]):
        ax.set_xscale("log")
        xlabel += " (log scale)"
    if _needs_log(df["v2"]):
        ax.set_yscale("log")
        ylabel += " (log scale)"
    
    ax.scatter(df["v1"], df["v2"], alpha=0.4, s=20, edgecolors="none")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title("12-Hour Window: Scatter Plot")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_12hr_heatmap(df, out_path, metric1_name="metric1", metric2_name="metric2", bins=30):
    if df.empty or len(df) < 10:
        return
    
    v1, v2 = df["v1"].values, df["v2"].values
    use_log_x, use_log_y = _needs_log(df["v1"]), _needs_log(df["v2"])
    
    if use_log_x:
        v1_pos = v1[v1 > 0]
        xedges = np.logspace(np.log10(v1_pos.min()), np.log10(v1_pos.max()), bins + 1) if len(v1_pos) > 0 else np.linspace(v1.min(), v1.max(), bins + 1)
    else:
        xedges = np.linspace(v1.min(), v1.max(), bins + 1)
    
    if use_log_y:
        v2_pos = v2[v2 > 0]
        yedges = np.logspace(np.log10(v2_pos.min()), np.log10(v2_pos.max()), bins + 1) if len(v2_pos) > 0 else np.linspace(v2.min(), v2.max(), bins + 1)
    else:
        yedges = np.linspace(v2.min(), v2.max(), bins + 1)
    
    v1_clean = v1[(v1 > 0) & (v2 > 0)] if (use_log_x or use_log_y) else v1
    v2_clean = v2[(v1 > 0) & (v2 > 0)] if (use_log_x or use_log_y) else v2
    
    counts, _, _ = np.histogram2d(v1_clean, v2_clean, bins=[xedges, yedges])
    
    fig, ax = plt.subplots(figsize=(10, 8))
    xlabel = metric1_name
    ylabel = metric2_name
    if use_log_x:
        ax.set_xscale("log")
        xlabel += " (log scale)"
    if use_log_y:
        ax.set_yscale("log")
        ylabel += " (log scale)"
    
    im = ax.imshow(counts.T, origin="lower", aspect="auto", extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap="YlOrRd")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title("12-Hour Window: 2D Heatmap")
    plt.colorbar(im, ax=ax, label="Count")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()