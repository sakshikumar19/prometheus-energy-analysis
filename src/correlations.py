import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

def normalize_series(s):
    if s.std() == 0:
        return s
    return (s - s.mean()) / s.std()

def compute_correlations(df, use_norm=False):
    clean = df[["v1", "v2"]].dropna()
    if clean.empty:
        return None

    v1 = clean["v1"].values
    v2 = clean["v2"].values

    if use_norm:
        v1 = normalize_series(pd.Series(v1)).values
        v2 = normalize_series(pd.Series(v2)).values

    pear = pearsonr(v1, v2)
    spear = spearmanr(v1, v2)

    return {
        "pearson_r": pear[0],
        "pearson_p": pear[1],
        "spearman_r": spear[0],
        "spearman_p": spear[1],
        "n": len(clean)
    }

def lag_correlation(df, max_lag=10):
    clean = df[["datetime", "v1", "v2"]].dropna().copy()
    if clean.empty or len(clean) < max_lag * 2:
        return None

    clean = clean.sort_values("datetime").reset_index(drop=True)
    v1 = clean["v1"].values
    v2 = clean["v2"].values

    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            shifted_v2 = v2
        elif lag > 0:
            shifted_v2 = np.concatenate([np.full(lag, np.nan), v2[:-lag]])
        else:
            shifted_v2 = np.concatenate([v2[-lag:], np.full(-lag, np.nan)])

        valid = ~(np.isnan(v1) | np.isnan(shifted_v2))
        if valid.sum() < 100:
            continue

        r, p = pearsonr(v1[valid], shifted_v2[valid])
        results.append({"lag": lag, "corr": r, "p": p})

    if not results:
        return None

    lags_df = pd.DataFrame(results)
    best = lags_df.loc[lags_df["corr"].abs().idxmax()]
    return {
        "best_lag": int(best["lag"]),
        "best_corr": float(best["corr"]),
        "best_p": float(best["p"]),
        "all_lags": lags_df
    }

def rate_correlation(df):
    clean = df[["datetime", "v1", "v2"]].dropna().sort_values("datetime").reset_index(drop=True)
    if len(clean) < 10:
        return None

    v1_delta = clean["v1"].diff().dropna()
    v2_delta = clean["v2"].diff().dropna()
    
    min_len = min(len(v1_delta), len(v2_delta))
    if min_len < 10:
        return None

    v1_delta = v1_delta.iloc[:min_len].values
    v2_delta = v2_delta.iloc[:min_len].values
    
    valid = ~(np.isnan(v1_delta) | np.isnan(v2_delta))
    if valid.sum() < 10:
        return None

    r, p = pearsonr(v1_delta[valid], v2_delta[valid])
    return {"corr": r, "p": p, "n": valid.sum()}
