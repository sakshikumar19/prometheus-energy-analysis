# Disk I/O vs Power Analysis Summary

## What is done

Analyzed disk I/O activity and power consumption from prometheus to see if they're related. The idea is that if I/O activity predicts power usage, we could use that for better energy scheduling.

## The Data

- **File 1**: Disk I/O metrics (node_disk_io_time_seconds_total) - measures how much time the disk spends doing I/O
- **File 2**: Power metrics (rPDULoadStatusLoad) - actual power draw in watts

Started with 4321 points from each metric. After matching up timestamps, got 1441 aligned time points.

## Key findings

### Overall correlation

The two metrics show a **weak negative correlation** of -0.095. The p-value is 0.0003, which means this relationship is statistically real (not random chance), but it's small.

When disk I/O increases, power actually goes down a bit. That's weird, you'd expect more I/O to use more power. But the connection is weak anyway, so I don't read too much into it.

### Time lag matters

The best correlation happens at **lag -20** (r = -0.13). Lag -20 means comparing current disk I/O to power from 20 time steps earlier.

This hints that power might respond to I/O changes with a delay. Or maybe power at some point affects I/O later. Either way, looking at them at the same time misses the connection.

### Rate of change

Also checked how fast values change (deltas). Sometimes the changes match up better than the raw numbers. Useful for catching short activity bursts.

### Rolling correlation

Instead of one correlation number, I calculated it over rolling 30-point windows. Shows how the relationship shifts over time.

- Mean rolling correlation: -0.057
- Standard deviation: 0.466
- Range: from -0.927 to +0.071

That high variance means the relationship jumps around. Sometimes strongly negative, sometimes slightly positive. The connection depends on what else is going on at that moment.

## What the numbers could mean

**V1 (Disk I/O)**: Numbers around 4.6 billion. These are cumulative I/O time in secs, keeps ticking up.

**V2 (Power)**: Numbers around 11,000-12,000 watts. Actual power draw from the PDU.

The scale difference (billions vs thousands) doesn't affect correlation as I was just looking at whether patterns match.

## The visualizations

### 1. Timeseries plot (`timeseries.png`)

Both metrics plotted over time. Different y-axes because the scales are so different. Not sure if I can eyeball whether they move together.

### 2. Scatter plot (`scatter.png`)

Each dot is one time step. X is disk I/O, Y is power. A strong relationship would show a clear line or curve. This one's pretty scattered, which matches the weak correlation we found.

### 3. Rolling correlation (`rolling_corr.png`)

30-point correlation over time. It bounces between negative and positive. The spikes are moments when they were more connected.

### 4. Lag analysis (`lag_analysis.png`)

Correlation at different time shifts. Red star marks the best one (lag -20). Basically it shows how correlation changes when we slide one metric forward or backward in time.

## Output files

**rolling_corr.csv**: The aligned data with rolling averages and correlations. First ~30 rows have empty rolling values as need enough points before I can start computing.

Columns:
- `datetime`: timestamp
- `v1`: disk I/O value
- `v2`: power value
- `v1_roll`: 30-point rolling average of disk I/O
- `v2_roll`: 30-point rolling average of power
- `roll_corr`: rolling correlation for that window

## Conclusion

What this means for energy work:

1. **Weak connection overall**: Power doesn't follow disk I/O directly. Other stuff is happening.

2. **Timing matters**: That -20 lag could be useful. If I/O at time T predicts power at T+20, we could schedule around it.

3. **It varies**: The relationship isn't steady. Sometimes they match up well, sometimes not at all. Depends on what else is running.

## Next Steps

- Combine with other metrics (CPU, memory) to build a better picture
- Find out why the relationship is negative (counterintuitive)
- Segregate for different machines!