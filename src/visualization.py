import matplotlib.pyplot as plt

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