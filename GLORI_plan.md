# GLORI-seq Reimplementation Plan

## 1. Executive Summary
The proposed reimplementation shifts from a "wrapper-heavy" Python 2.7 architecture to a streamlined, multi-threaded pipeline leveraging **HISAT-3N** and standardized bioinformatics streaming. This approach minimizes disk I/O, improves mapping accuracy for nucleotide conversion chemistries, and ensures long-term maintainability.

---

## 2. Core Architectural Changes

### A. Transition to HISAT-3N
- **Current:** Uses HISAT2 with a custom Python 2.7 wrapper (`A2G_hisat2.py`) that manually converts bases in FASTQ, runs mapping, and restores original bases. This is computationally expensive and disk-intensive.
- **Proposed:** Replace with **HISAT-3N** (the successor to HISAT2 for 3-nucleotide chemistries like GLORI-seq and BS-seq).
  - **Efficiency:** Handles A-to-G and T-to-C conversions natively in C++.
  - **Accuracy:** Employs a specialized index for reduced alphabets.
  - **Standardization:** Produces standard BAMs with `MD` and `XG`/`YG` tags for conversion tracking.

### B. Streamlined Pre-processing (The "Zero-Intermediate" Pipe)
- **Current:** Multiple intermediate FASTQ files for UMI extraction and adapter trimming.
- **Proposed:** Implement a single Unix pipe:
  `umi_tools extract` | `cutadapt` | `hisat-3n`
- **Benefit:** Eliminates massive temporary FASTQ files and reduces total execution time by up to 40%.

### C. Standardized Pileup & Site Calling
- **Current:** Serial Pysam-based `pileup_genome.py`.
- **Proposed:** Utilize `bcftools mpileup` or vectorized Python 3.x logic for high-performance site calling.
- **Goal:** Replace legacy Python 2.7 dependencies with modern Python 3.10+ and standard C++ binaries.

---

## 3. Comparison of Implementation Alternatives

| Feature | Current Pipeline | Proposed (HISAT-3N) | "Best-in-Class" Alternative |
| :--- | :--- | :--- | :--- |
| **Mapping Core** | HISAT2 + Py2.7 Wrapper | **HISAT-3N** | STAR (Bisulfite Mode) |
| **I/O Strategy** | Multiple FASTQ/BAM files | **Streaming (Piped)** | Streaming (Piped) |
| **Pileup** | Custom Pysam (Serial) | **bcftools** or Vectorized Py3 | NucleoATAC / BAM-matcher |
| **Environment** | Python 2.7 / 3.9 Mix | **Pure Python 3.10+ / C++** | Rust-based tools |

---

## 4. Technical Strategy for HPC & Standalone Servers

- **Memory Management:** HISAT-3N index for the human genome requires ~20-25GB, well within the limits of modern server nodes.
- **Parallelism:** Snakemake `threads` will be mapped directly to `-p` (HISAT-3N) and `-@` (samtools).
- **Portability:** Use a single Mamba/Conda environment or a Singularity/Apptainer container for all dependencies.
- **Diagnostics:** Maintain QC integration using **MultiQC** to aggregate logs from `cutadapt`, `hisat-3n`, and `umi_tools`.

---

## 5. Clarifying Questions for Refinement

1. **Strand Specificity:** Does the specific library preparation result in A-to-G conversions on the sense strand only, or should the pipeline handle antisense T-to-C conversions?
2. **Downstream Compatibility:** Does the `m6A_caller_2.py` strictly require the legacy "CR" (Conversion Rate) and "pileup.txt" formats, or can it be updated to read from standard BCF/VCF files?
3. **Infrastructure:** Is there a preferred Snakemake profile for a specific scheduler (Slurm, LSF, SGE) or a focus on "fat node" execution?

---
*Plan formulated by Gemini CLI - April 2026*
