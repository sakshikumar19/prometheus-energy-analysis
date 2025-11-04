# Analysis Summary

Correlation results were compared across two machines (**atlaslab18** and **wn1205080**) for a 12-hour window (2025-07-31 23:00 to 2025-08-01 11:00 UTC).

---

## atlaslab18.blackett.manchester.ac.uk

### Strong correlations
**Network RX vs TX Bytes**  
- Pearson r = 0.99, Spearman r = 1.00  
- Indicates symmetric bidirectional traffic  

**Disk Read vs Write Bytes**  
- Pearson r = 0.90, Spearman r = 0.87  
- Reads and writes occur together, likely due to batch workloads  

### Weak correlations
**Disk IO Time vs Load** – r ≈ 0.08–0.09, not meaningful  
**Memory Available vs Load** – Pearson r = −0.03, Spearman r = −0.26  
Memory drops slightly as load rises but not linearly  

### No correlation
**Memory Cached vs Load**, **Processes Blocked vs Load**, **Processes Running vs Load** all near r = 0.  
Load appears driven more by I/O wait and CPU queue depth than process count.

### Missing data
**Network RX Errors vs Drops:** NaN — both zero (no errors observed)

---

## wn1205080 (Power analysis)

**Power Usage Cumulative vs Load**  
- Pearson r = 0.35, Spearman r = 0.43  
- Correlation inflated by cumulative time trend  

**Power Usage Cumulative vs Disk IO Time**  
- Pearson r = 0.999, Spearman r = 1.00  
- Perfect but fake correlation from both metrics being monotonic  

---

## Problems found
1. Cumulative metrics inflated correlations since they all increase over time  
2. Large value ranges made plots unreadable on linear scales  
3. Counter metrics required rate conversion for valid comparisons  

---