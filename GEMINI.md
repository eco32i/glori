# GLORI Snakemake Workflow

A Snakemake-based bioinformatics pipeline for GLORI-seq and RNA-m5C analysis, wrapping the `GLORI_pipeline` and `RNA-m5C` repositories. It automates the process of adapter trimming, UMI extraction, A-to-G converted alignment (using HISAT2), pileup generation, and m6A/m5C site calling.

## Project Overview

- **Purpose:** Identification of RNA modifications (m6A/m5C) from GLORI-seq data.
- **Core Technology:** [Snakemake](https://snakemake.readthedocs.io/) 8.x, Python 2.7 (legacy scripts), Python 3.9 (m6A caller).
- **Submodules:**
  - `GLORI_pipeline`: Custom scripts for A2G-converted HISAT2 mapping and pileup.
  - `RNA-m5C`: Metadata generation and core logic from the Zhang lab.

## Prerequisites

- **Conda:** Used for software deployment (defined in `envs/`).
- **HISAT2 v2.1.0:** MUST be compiled manually. The pipeline scripts (specifically `A2G_hisat2.py`) expect a specific directory structure (e.g., finding `extract_exons.py` relative to the binary).
  - **Build Instruction:**
    ```bash
    git clone --branch v2.1.0 --depth 1 https://github.com/DaehwanKimLab/hisat2
    cd hisat2 && make
    ```
- **Cloning:** Use `--recurse-submodules` to include the nested dependencies.

## Configuration

Modify `config.yaml` to specify your data and environment paths:
- `hisat2_path`: Absolute path to the manually compiled HISAT2 directory.
- `reference_fasta`/`reference_gtf`: Genome and annotation files.
- `sample_to_fastq`: Mapping of sample names to input FASTQ files.

## Key Commands

### Execution
Run the full pipeline using the `evaluate_calls` target:
```bash
snakemake --cores 10 --software-deployment-method conda --conda-prefix <path_to_cache> evaluate_calls
```

### Common Targets
- `hisat2_index`: Build the custom HISAT2 index.
- `pileups`: Generate pileup files for all samples.
- `m6A_caller`: Perform site calling.
- `evaluate_calls`: Add reliability labels to calls.

### Development & Debugging
- **Dry Run:** `snakemake -n`
- **Visualization:** `snakemake --dag | dot -Tsvg > dag.svg`

## Development Conventions

- **Legacy Compatibility:** Many core scripts in `GLORI_pipeline` and `RNA-m5C` require Python 2.7. These are managed via the `envs/python_2.7.16.yaml` environment.
- **Modularity:** Custom logic is split between the root `scripts/` directory and submodules. Avoid modifying submodule files directly; prefer wrapping them in Snakemake rules.
- **Memory Requirements:** HISAT2 indexing and pileup generation are memory-intensive. Ensure at least 70GB+ RAM is available for human genome processing.
