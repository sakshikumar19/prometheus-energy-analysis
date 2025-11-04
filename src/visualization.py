import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_12hr_scatter(df, out_path, metric1_name="metric1", metric2_name="metric2"):
    if df.empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(df["v1"], df["v2"], alpha=0.4, s=20, edgecolors="none")
    ax.set_xlabel(metric1_name)
    ax.set_ylabel(metric2_name)
    ax.set_title("12-Hour Window: Scatter Plot")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_12hr_heatmap(df, out_path, metric1_name="metric1", metric2_name="metric2", bins=30):
    if df.empty or len(df) < 10:
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    counts, xedges, yedges = np.histogram2d(df["v1"], df["v2"], bins=bins)
    im = ax.imshow(counts.T, origin="lower", aspect="auto", extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap="YlOrRd")
    ax.set_xlabel(metric1_name)
    ax.set_ylabel(metric2_name)
    ax.set_title("12-Hour Window: 2D Heatmap")
    plt.colorbar(im, ax=ax, label="Count")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()