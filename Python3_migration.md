# Python 3 Migration Plan: GLORI-Seq Pipeline

## 1. Feasibility Overview
The project currently relies on Python 2.7 for its core alignment and pileup processing (managed via `envs/python_2.7.16.yaml`). Several downstream scripts for m6A calling already use Python 3.9, indicating a fragmented codebase. Porting the entire pipeline to Python 3 is **highly feasible** as all core dependencies (`pysam`, `numpy`, `scipy`, `biopython`) have robust Python 3 support.

## 2. Major Changes Required

| Category | Changes |
| :--- | :--- |
| **Syntax** | Replace `print` statements with `print()` functions. Replace `xrange()` with `range()`. |
| **Data Types** | Replace `.iteritems()`, `.itervalues()`, and `.iterkeys()` with `.items()`, `.values()`, and `.keys()`. |
| **String & Bytes** | **(Critical)** Handle the shift from `str` (bytes in Py2) to `Unicode` (Py3). Bioinformatics data (BAM/FASTQ/GZIP) must be handled as `bytes` or explicitly decoded to `str`. |
| **File I/O** | Update `file()` to `open()`. Update `gzip.open(..., 'r')` to `gzip.open(..., 'rt')` for text-mode reading of compressed files. |
| **Math** | Ensure integer division uses `//` instead of `/` where legacy behavior is required. |
| **Libraries** | Update `pysam` calls to handle the transition from bytes to strings for sequence data and tags (e.g., `get_tag("YG")` returning `b"A2G"` instead of `"A2G"`). |

## 3. Challenges and Compatibility Issues

*   **Pysam Transition:** In Python 3, `pysam` attributes like `query_sequence` and `query_name` may return `bytes` depending on the version and opening mode. Comparisons like `if tag == "A2G":` will fail if `tag` is `b"A2G"`.
*   **Pickling/Multiprocessing:** The `pileup_genome.py` script uses `multiprocessing`. Python 3 changed the default start method for multiprocessing on some platforms and is stricter about what can be pickled.
*   **Database (SQLite3):** Scripts using `sqlite3` (like `format_pileups.py`) will need to handle Unicode strings correctly, as Python 3 is more rigorous about text vs. binary data in databases.
*   **Dependency Versions:** Moving to modern `numpy` (1.20+) or `scipy` may trigger deprecation warnings or errors if the code uses very old API features from the 2017-era versions currently specified.

## 4. Side Effects

*   **Performance:** Python 3 is generally faster for many operations, but the overhead of Unicode handling for massive genomic strings can occasionally increase memory usage or slow down string-heavy processing if not optimized.
*   **Index Stability:** Changes in how strings are sorted or hashed (though unlikely to affect genomic coordinates) should be verified to ensure output stability.

## 5. Recommended Action Plan (Strategy)

1.  **Consolidate Environments:** Create a single `envs/glori_py3.yaml` containing all dependencies (Python 3.10+, Pysam 0.20+, etc.).
2.  **Automated Conversion:** Run `2to3` on the `scripts/`, `GLORI_pipeline/`, and `RNA-m5C/` directories to handle basic syntax changes.
3.  **Manual Refinement:** Conduct a surgical review of all `pysam` and `gzip` interactions to ensure `bytes` vs. `str` consistency.
4.  **Validation:** Use the `test1`/`test2` datasets mentioned in `config.yaml` to verify that the Python 3 pipeline produces bit-for-bit identical (or scientifically equivalent) results to the Python 2 version.

## 6. Assessment
The port is recommended to ensure long-term maintainability, as Python 2.7 has been end-of-life since 2020 and many high-performance computing (HPC) environments are phasing out support for it.
