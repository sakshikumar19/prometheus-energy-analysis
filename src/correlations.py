import pandas as pd
from scipy.stats import pearsonr, spearmanr

def compute_correlations(df):
    if df[["v1", "v2"]].dropna().empty:
        return None

    pear = pearsonr(df["v1"], df["v2"])
    spear = spearmanr(df["v1"], df["v2"])

    return {
        "pearson_r": pear[0],
        "pearson_p": pear[1],
        "spearman_r": spear[0],
        "spearman_p": spear[1],
        "n": len(df)
    }
