# Pipeline Results Documentation

This document explains the format of the output files produced by the modernized GLORI-seq pipeline.

## `results/m6A_calls_modern.csv`

This file contains the merged m6A site calls across all samples.

### Column Definitions

| Column Name | Description |
| :--- | :--- |
| **ID** | Unique identifier for the site: `chrom@pos@strand` (1-based genomic coordinates). |
| **GeneID** | Placeholder for Gene ID annotation (currently `NA`). |
| **GeneName** | Placeholder for Gene Name annotation (currently `NA`). |
| **coverage** | Total read depth at the genomic position. |
| **modified_count** | Number of reads remaining unconverted ('A' on + strand, 'T' on - strand). |
| **ratio** | The calculated **m6A level** (`modified_count / coverage`). |
| **p_val** | P-value from a binomial test against the global non-conversion rate. |
| **bg_rate** | The **Non-Conversion Rate (nonCR)** for that sample. |

---

## Conversion Rate (CR) Information

The **Conversion Rate (CR)** is the efficiency of the chemical deamination (A→G transition). In this pipeline:

*   **Relationship:** `Conversion Rate = 1 - bg_rate`.
*   **Calculation:** The pipeline estimates a global background rate for each sample by sampling the first 100,000 reads and calculating the frequency of A→G (or T→C) transitions at all reference A/T sites.
*   **Statistical Use:** The `bg_rate` is used as the null hypothesis probability in the binomial test. A low p-value indicates that the number of unconverted bases at a specific site is significantly higher than the global "noise" caused by chemical or enzymatic inefficiency.
