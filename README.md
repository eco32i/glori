# GLORI-seq Snakemake Workflow (v2.0)

A modernized, high-performance bioinformatics pipeline for GLORI-seq (A-to-G conversion) analysis. This version leverages native HISAT-3N alignment and a streamlined "zero-intermediate" architecture.

## Key Features

- **HISAT-3N Integration:** Native 3-nucleotide mapping for high accuracy and speed.
- **Zero-Intermediate Files:** Piped pre-processing (`umi_tools` -> `cutadapt` -> `hisat-3n`) minimizes disk I/O.
- **Parallelized Site Calling:** Genome-wide m6A calling is distributed across available CPUs.
- **HPC Ready:** Includes profiles for Local (Fat-node) and Slurm environments.

## Prerequisites

- **Conda / Mamba:** Used for software deployment.
- **Snakemake 8.x:** Core workflow engine.

## Installation

```bash
git clone --recurse-submodules https://github.com/gp-micro/glori
cd glori
```

## Configuration

Modify `config.yaml` to specify your data and reference paths:

```yaml
results_dir: "results"
sample_to_fastq:
    "sample1": "data/sample1.fastq.gz"
    "sample2": "data/sample2.fastq.gz"

reference_fasta: "path/to/genome.fa"
reference_gtf: "path/to/annotation.gtf"
```

## Running the Pipeline

### Local / Fat-Node (256 CPU)
```bash
snakemake --profile profiles/local --use-conda
```

### Slurm Cluster
```bash
snakemake --profile profiles/slurm --use-conda
```

## Pipeline Steps

1. **Indexing:** Builds a HISAT-3N index with splice site and exon information.
2. **Mapping:** Performs UMI extraction, adapter trimming, and 3N alignment in a single stream.
3. **Deduplication:** Removes PCR duplicates using UMIs.
4. **Site Calling:** Calls m6A sites using a binomial test against estimated background conversion rates.
5. **QC:** Aggregates logs into a single MultiQC report.

## Directory Structure

- `Snakefile`: Main workflow definition.
- `scripts/`: Custom Python 3.11 logic for site calling and merging.
- `envs/`: Unified Conda environment definition.
- `profiles/`: Cluster and local execution profiles.
- `results/`: output directory for BAMs, VCFs, and reports.
- `results/ground_truth/`: Original results used for verification.

---
*Maintained by Gemini CLI - April 2026*
