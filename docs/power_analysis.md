# Power Analysis

## Background
- Mentor feedback: cumulative power is not suitable for correlation plots because it is monotonically increasing.
- Provided alternative: CSVs with power deltas at 10s, 1min, 5min, 10min, 60min.
- Goal: correlate power deltas (kWh over interval) against system metrics (load, disk IO time) on machine `wn3803100` which has higher variance.

## Data and method
- Data location: `data/power/*.csv` in wide format (`machine, <epoch1>, <epoch2>, ...`).
- Loader: added CSV support (melt to long), reused existing pipeline (align -> correlate -> plot).
- Alignment: resamples by the coarser cadence (e.g., 60min when mixing 60min deltas with 1min load) to avoid oversampling sparse power points.
- Visualization: automatic log/log–log scaling when ranges are wide, robust axis limits (1–99th percentiles), smaller and semi-transparent points, higher-contrast heatmaps.

## Results (wn3803100)
Time window: 2025-07-31 23:00 to 2025-08-01 11:00 UTC.

- Power Delta (60min) vs Load (1m): Pearson 0.9993, Spearman 0.6582, N≈12
- Power Delta (60min) vs Disk IO Time: Pearson -0.5767, Spearman -0.3067, N≈12
- Power Delta (10min) vs Load (1m): Pearson 0.9968, Spearman 0.6869
- Power Delta (10min) vs Disk IO Time: Pearson -0.4065, Spearman -0.3007
- Power Delta (5min) vs Load (1m): Pearson 0.9939, Spearman 0.6574
- Power Delta (5min) vs Disk IO Time: Pearson -0.3473, Spearman -0.2310
- Power Delta (1min) vs Load (1m): Pearson 0.9209, Spearman 0.6087
- Power Delta (1min) vs Disk IO Time: Pearson -0.1889, Spearman -0.1866

Observations:
- Power deltas are strongly positively correlated with load across all cadences (Pearson 0.92–1.00, Spearman 0.61–0.69). This persists even with coarser alignment and rate-like inputs.
- Power deltas are weakly to moderately negatively correlated with disk IO time (Pearson -0.19 to -0.58, Spearman -0.19 to -0.31), weakening as cadence gets finer.
- At 60min cadence, N is small (≈12). Spearman p-values are less robust there; hence use 10min/5min for stability.

## Comparison with earlier findings (docs/improvement_analysis.md)
- Earlier, converting cumulative power to rates removed a spurious near-perfect correlation vs disk IO time (r≈0). That remains correct.
- Using mentor-provided deltas now confirms a strong relationship with load, not with disk IO time. This is consistent with the rate-based conclusion: power responds more to CPU/memory pressure than disk IO saturation in this window.

## Takeaways
- Power deltas correlate strongly with load across cadences; the relationship is persistent after fixing cumulative artifacts.
- Disk IO time shows weak to moderate negative correlation with power deltas in this window.
- Coarser deltas give fewer points (e.g., 60min) and less robust rank tests; 10min/5min offer a better balance.

## Next step
- I think adding a time-series view for power delta vs load to inspect temporal structure.