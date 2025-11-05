import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def _needs_log(s):
    clean = s.dropna()
    return len(clean) > 0 and clean.min() > 0 and clean.max() / clean.min() > 100

def _robust_limits(s, low_q=0.01, high_q=0.99):
    clean = s.dropna()
    if len(clean) == 0:
        return None
    lo = np.quantile(clean, low_q)
    hi = np.quantile(clean, high_q)
    if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
        return None
    return (lo, hi)

def plot_12hr_scatter(df, out_path, metric1_name="metric1", metric2_name="metric2"):
    if df.empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    xlabel = metric1_name
    ylabel = metric2_name
    x_log = _needs_log(df["v1"])
    y_log = _needs_log(df["v2"])
    # If either axis clearly benefits from log and both are positive, use log-log
    if (x_log or y_log) and (df["v1"].min() > 0) and (df["v2"].min() > 0):
        x_log = True
        y_log = True
    if x_log:
        ax.set_xscale("log")
        xlabel += " (log scale)"
    if y_log:
        ax.set_yscale("log")
        ylabel += " (log scale)"
    
    # Smaller, more transparent points improve readability in dense regions
    ax.scatter(df["v1"], df["v2"], s=12, edgecolors="none", color="crimson")
    # If not log-scaled, tighten axes using robust percentiles so outliers don't dominate
    if ax.get_xscale() == "linear":
        lim = _robust_limits(df["v1"]) 
        if lim:
            ax.set_xlim(lim)
    if ax.get_yscale() == "linear":
        lim = _robust_limits(df["v2"]) 
        if lim:
            ax.set_ylim(lim)
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
    # If either axis benefits from log and both are positive, use log-log
    if (use_log_x or use_log_y) and (np.min(v1) > 0) and (np.min(v2) > 0):
        use_log_x = True
        use_log_y = True
    # Build bin edges using robust limits on linear scale
    if use_log_x:
        v1_pos = v1[v1 > 0]
        xedges = np.logspace(np.log10(v1_pos.min()), np.log10(v1_pos.max()), bins + 1) if len(v1_pos) > 0 else np.linspace(np.min(v1), np.max(v1), bins + 1)
    else:
        lim = _robust_limits(pd.Series(v1))
        xmin, xmax = (lim if lim else (np.min(v1), np.max(v1)))
        xedges = np.linspace(xmin, xmax, bins + 1)
    
    if use_log_y:
        v2_pos = v2[v2 > 0]
        yedges = np.logspace(np.log10(v2_pos.min()), np.log10(v2_pos.max()), bins + 1) if len(v2_pos) > 0 else np.linspace(np.min(v2), np.max(v2), bins + 1)
    else:
        lim = _robust_limits(pd.Series(v2))
        ymin, ymax = (lim if lim else (np.min(v2), np.max(v2)))
        yedges = np.linspace(ymin, ymax, bins + 1)
    
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
    
    # Higher-contrast palette for better readability
    im = ax.imshow(counts.T, origin="lower", aspect="auto", extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap="viridis")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title("12-Hour Window: 2D Heatmap")
    plt.colorbar(im, ax=ax, label="Count")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()