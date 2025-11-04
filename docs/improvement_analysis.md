# Improvement Analysis

Comparison of results before and after adding **rate conversion** and **log scaling**.

The files with the `_1` suffix represent the **newly processed versions** of the same time window (e.g., `2025-07-31T23-00_to_2025-08-01T11-00_1` is the updated version of `2025-07-31T23-00_to_2025-08-01T11-00`).

---

## Power Metrics: Major Fix

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Power vs Load (Pearson / Spearman) | 0.35 / 0.43 | 0.00 / 0.00 | Fake correlation removed |
| Power vs Disk IO Time (Pearson / Spearman) | 0.999 / 1.000 | -0.01 / -0.00 | Perfect but false correlation fixed |

**Interpretation:** Both metrics were cumulative and rose over time, creating spurious correlations.  
After rate conversion, correlation correctly drops to near zero, indicating no true relationship.

---

## Counter Metrics: Normalized

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Network RX vs TX Bytes | 0.99 / 1.00 | 0.27 / 0.45 | More realistic correlation |
| Disk Read vs Write Bytes | 0.90 / 0.86 | 0.63 / 0.05 | Linear trend corrected |

**Interpretation:**  
Rate conversion removed inflated cumulative correlations.  
RX/TX now show a moderate and realistic relationship.  
Disk Read/Write remain somewhat related (Pearson ≈0.63) but the non-linear pattern weakens the Spearman correlation.

---

## Gauge Metrics: Unchanged
Metrics like **Disk IO Time vs Load**, **Mem Available vs Load** and **Procs Running vs Load** remained identical before and after.  
This is expected since gauge metrics are not cumulative and should not be rate-converted.

---

## Why Rate Conversion Was Added

**Problem:** Cumulative metrics such as `*_total` or `*CumulativeWattage` always increase over time, creating artificial correlations due to shared time trends.  
**Fix:** Converedt cumulative values to **rates** (`diff(value) / diff(time)`), removing time dependency.  
**Detection:** Metrics ending in `_total` or showing ≥95% non-decreasing behavior are treated as counters, with counter resets handled automatically.

---

## Why Log Scaling Was Added

**Problem:** Some metrics span several orders of magnitude (e.g., bytes from 1 to 1,000,000), causing most points to cluster near zero on linear scales.  
**Fix:** Applied log scaling when the value range exceeds roughly 100× (for positive values only).  
Axes are labeled with “(log scale)” when applied, improving readability for wide-range data.

---


## Conclusion

Rate conversion and log scaling significantly improved correlation accuracy and visualization quality.  
Cumulative time trends no longer inflate correlations and metric relationships now reflect real system behavior.