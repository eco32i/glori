configfile: "config.yaml"

import os

# Global variables
SAMPLES = list(config["sample_to_fastq"].keys())
REF_FASTA = config["reference_fasta"]
REF_GTF = config["reference_gtf"]
RESULTS_DIR = config["results_dir"]
TOTAL_CORES = 256
MAP_THREADS = 120 if len(SAMPLES) <= 2 else 32
INDEX_THREADS = 128

rule all:
    input:
        os.path.join(RESULTS_DIR, "multiqc/multiqc_report.html"),
        os.path.join(RESULTS_DIR, "comparison.txt")

rule compare_results:
    input:
        modern = os.path.join(RESULTS_DIR, "m6A_calls_modern.csv"),
        gt = "results/ground_truth/m6A_calls.csv"
    output:
        os.path.join(RESULTS_DIR, "comparison.txt")
    conda: "envs/glori_v2.yaml"
    shell:
        "python3 scripts/compare_results.py {input.modern} {input.gt} > {output}"

rule hisat3n_index:
    input:
        fasta = REF_FASTA,
        gtf = REF_GTF
    output:
        directory(os.path.join(RESULTS_DIR, "index/hisat3n"))
    threads: INDEX_THREADS
    log: "logs/hisat3n_index.log"
    conda: "envs/glori_v2.yaml"
    shell:
        """
        mkdir -p {output}
        # Extract splice sites and exons
        hisat2_extract_splice_sites.py {input.gtf} > {output}/splice_sites.txt
        hisat2_extract_exons.py {input.gtf} > {output}/exons.txt
        
        # Build 3N index
        hisat-3n-build -p {threads} \
            --ss {output}/splice_sites.txt \
            --exon {output}/exons.txt \
            {input.fasta} {output}/hisat3n &> {log}
        """

rule extract_umi:
    input:
        fastq = lambda wildcards: config["sample_to_fastq"][wildcards.sample]
    output:
        fastq = temp(os.path.join(RESULTS_DIR, "tmp/{sample}.extracted.fq.gz"))
    log: "logs/umi_extract/{sample}.log"
    conda: "envs/glori_v2.yaml"
    shell:
        "umi_tools extract -I {input.fastq} -S {output.fastq} -p NNNNNNNNNNNN --log={log}"

rule trim_adapters:
    input:
        fastq = os.path.join(RESULTS_DIR, "tmp/{sample}.extracted.fq.gz")
    output:
        fastq = temp(os.path.join(RESULTS_DIR, "tmp/{sample}.trimmed.fq.gz"))
    log: "logs/cutadapt/{sample}.log"
    conda: "envs/glori_v2.yaml"
    shell:
        "cutadapt -a AGATCGGAAGAGCGTCGTG --max-n 0 --trimmed-only -e 0.1 -q 30 -m 30 -o {output.fastq} {input.fastq} &> {log}"

rule map_and_sort:
    input:
        fastq = os.path.join(RESULTS_DIR, "tmp/{sample}.trimmed.fq.gz"),
        index = os.path.join(RESULTS_DIR, "index/hisat3n")
    output:
        bam = os.path.join(RESULTS_DIR, "mapped/{sample}.sorted.bam")
    threads: MAP_THREADS
    log: "logs/mapping/{sample}.log"
    conda: "envs/glori_v2.yaml"
    shell:
        """
        HT_THREADS=$(( {threads} * 8 / 10 ))
        ST_THREADS=$(( {threads} * 2 / 10 ))
        zcat {input.fastq} \
        | hisat2-align-s --wrapper basic-0 -p $HT_THREADS \
            --3N --base-change A,G \
            --rna-strandness F \
            --no-unal \
            -U - \
            -x {input.index}/hisat3n \
        | samtools sort -@ $ST_THREADS -o {output.bam} - 2> {log}
        """

rule samtools_index:
    input:
        "{path}.bam"
    output:
        "{path}.bam.bai"
    conda: "envs/glori_v2.yaml"
    shell:
        "samtools index {input}"

rule umi_dedup:
    input:
        bam = os.path.join(RESULTS_DIR, "mapped/{sample}.sorted.bam"),
        bai = os.path.join(RESULTS_DIR, "mapped/{sample}.sorted.bam.bai")
    output:
        bam = os.path.join(RESULTS_DIR, "dedup/{sample}.dedup.bam")
    log: "logs/dedup/{sample}.log"
    conda: "envs/glori_v2.yaml"
    shell:
        "umi_tools dedup -I {input.bam} -S {output.bam} --log {log}"

rule call_m6a:
    input:
        bam = os.path.join(RESULTS_DIR, "dedup/{sample}.dedup.bam"),
        bai = os.path.join(RESULTS_DIR, "dedup/{sample}.dedup.bam.bai"),
        ref = REF_FASTA
    output:
        tsv = os.path.join(RESULTS_DIR, "calls/{sample}.m6A.tsv")
    threads: 32
    conda: "envs/glori_v2.yaml"
    shell:
        "python3 scripts/call_m6a_from_3n.py -i {input.bam} -f {input.ref} -o {output.tsv} -t {threads}"

rule merge_calls:
    input:
        tsvs = expand(os.path.join(RESULTS_DIR, "calls/{sample}.m6A.tsv"), sample=SAMPLES),
        gtf = REF_GTF
    output:
        csv = os.path.join(RESULTS_DIR, "m6A_calls_modern.csv")
    conda: "envs/glori_v2.yaml"
    shell:
        "python3 scripts/merge_and_annotate.py -i {input.tsvs} -g {input.gtf} -o {output.csv}"

rule multiqc:
    input:
        expand(os.path.join(RESULTS_DIR, "mapped/{sample}.sorted.bam"), sample=SAMPLES)
    output:
        os.path.join(RESULTS_DIR, "multiqc/multiqc_report.html")
    conda: "envs/glori_v2.yaml"
    shell:
        "multiqc --force logs/ -o {RESULTS_DIR}/multiqc/"
