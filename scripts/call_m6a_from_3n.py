#!/usr/bin/env python3
import pysam
import argparse
import scipy.stats
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import sys
import os
from concurrent.futures import ProcessPoolExecutor

def get_background_rates_fast(bam_path, ref_fasta, n_reads=100000):
    samfile = pysam.AlignmentFile(bam_path, "rb")
    fasta = pysam.FastaFile(ref_fasta)
    a_total, a_to_g = 0, 0
    t_total, t_to_c = 0, 0
    count = 0
    for read in samfile.fetch():
        if read.is_unmapped or read.is_secondary or read.is_supplementary: continue
        try:
            ref_seq = fasta.fetch(read.reference_name, read.reference_start, read.reference_end)
        except: continue
        read_seq = read.query_sequence
        for read_pos, ref_pos in read.get_aligned_pairs(matches_only=True):
            if ref_pos is None or read_pos is None: continue
            rel_pos = ref_pos - read.reference_start
            if rel_pos >= len(ref_seq): continue
            ref_base = ref_seq[rel_pos].upper()
            read_base = read_seq[read_pos].upper()
            if ref_base == 'A':
                a_total += 1
                if read_base == 'G': a_to_g += 1
            elif ref_base == 'T':
                t_total += 1
                if read_base == 'C': t_to_c += 1
        count += 1
        if count >= n_reads: break
    return a_to_g / max(1, a_total), t_to_c / max(1, t_total)

def process_pileup_segment(bam_path, ref_fasta, chrom, start, end, bg_a2g, bg_t2c, min_cov, p_cutoff):
    samfile = pysam.AlignmentFile(bam_path, "rb")
    fasta = pysam.FastaFile(ref_fasta)
    results = []
    for pileupcolumn in samfile.pileup(chrom, start, end, truncate=True, max_depth=10000):
        pos = pileupcolumn.pos
        ref_base = fasta.fetch(chrom, pos, pos+1).upper()
        if ref_base not in ['A', 'T']: continue
        counts = Counter([p.alignment.query_sequence[p.query_position] 
                         for p in pileupcolumn.pileups if not p.is_del and not p.is_refskip])
        coverage = sum(counts.values())
        if coverage < min_cov: continue
        if ref_base == 'A':
            modified_count = counts.get('A', 0)
            bg_err_rate = 1.0 - bg_a2g
            strand = '+'
        else: # T
            modified_count = counts.get('T', 0)
            bg_err_rate = 1.0 - bg_t2c
            strand = '-'
        ratio = modified_count / coverage
        p_val = scipy.stats.binomtest(modified_count, n=coverage, p=bg_err_rate, alternative='greater').pvalue
        if p_val <= p_cutoff:
            results.append({
                'chrom': chrom, 'pos': pos + 1, 'strand': strand, 'ref_base': ref_base,
                'coverage': coverage, 'modified_count': modified_count, 'ratio': ratio,
                'p_val': p_val, 'bg_rate': bg_err_rate
            })
    return results

def call_m6a_parallel(bam_path, ref_fasta, output_tsv, threads, min_cov=20, p_cutoff=1.0):
    bg_a2g, bg_t2c = get_background_rates_fast(bam_path, ref_fasta)
    samfile = pysam.AlignmentFile(bam_path, "rb")
    active_regions = []
    for chrom, length in zip(samfile.references, samfile.lengths):
        if samfile.get_index_statistics()[samfile.references.index(chrom)].mapped > 0:
            for start in range(0, length, 5000000):
                active_regions.append((chrom, start, min(start + 5000000, length)))
    all_results = []
    with ProcessPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(process_pileup_segment, bam_path, ref_fasta, c, s, e, bg_a2g, bg_t2c, min_cov, p_cutoff) 
                   for c, s, e in active_regions]
        for future in futures: all_results.extend(future.result())
    pd.DataFrame(all_results).to_csv(output_tsv, sep="\t", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--bam", required=True)
    parser.add_argument("-f", "--ref", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-t", "--threads", type=int, default=1)
    parser.add_argument("-c", "--min-cov", type=int, default=20)
    parser.add_argument("-p", "--pvalue", type=float, default=1.0)
    args = parser.parse_args()
    call_m6a_parallel(args.bam, args.ref, args.output, args.threads, args.min_cov, args.pvalue)
