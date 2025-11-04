import pandas as pd
from scipy.stats import pearsonr, spearmanr

def _normalize(s: pd.Series) -> pd.Series:
    std = s.std()
    if std == 0:
        return s
    return (s - s.mean()) / std

def compute_correlations(df, use_norm=False):
    clean = df[["v1", "v2"]].dropna()
    if clean.empty:
        return None

    v1 = clean["v1"].copy()
    v2 = clean["v2"].copy()

    if use_norm:
        v1 = _normalize(v1)
        v2 = _normalize(v2)

    r_p = pearsonr(v1, v2)
    r_s = spearmanr(v1, v2)

    return {
        "pearson_r": r_p[0],
        "pearson_p": r_p[1],
        "spearman_r": r_s[0],
        "spearman_p": r_s[1],
        "n": len(clean)
    }
