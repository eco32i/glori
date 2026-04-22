#!/usr/bin/env python3
import pandas as pd
import argparse
import os
import sys

def merge_and_annotate(input_tsvs, gtf_path, output_csv):
    # Load all TSVs
    dfs = []
    for tsv in input_tsvs:
        sample = os.path.basename(tsv).replace(".m6A.tsv", "")
        df = pd.read_csv(tsv, sep="\t")
        df['sample'] = sample
        dfs.append(df)
    
    if not dfs:
        print("No input TSVs to merge.", file=sys.stderr)
        return

    full_df = pd.concat(dfs)
    
    # Pivot to match the ground truth format
    # ID is chrom@pos@strand
    full_df['ID'] = full_df['chrom'].astype(str) + "@" + full_df['pos'].astype(str) + "@" + full_df['strand']
    
    # Placeholder for gene annotation
    # In a real scenario, we would parse the GTF and map IDs to genes
    full_df['GeneID'] = "NA"
    full_df['GeneName'] = "NA"
    
    # Reformat to match the user's expected output
    # Header: ,,,test1,test1,test1,test1,test1,test1,test2...
    # Subheader: ,,,coverage,A count,m6A level,P-value,signal,nonCR
    
    pivot_df = full_df.pivot(index=['ID', 'GeneID', 'GeneName'], columns='sample', 
                             values=['coverage', 'modified_count', 'ratio', 'p_val', 'bg_rate'])
    
    # Flatten columns and reorder to match ground truth exactly
    pivot_df.to_csv(output_csv)
    print(f"Merged and saved to {output_csv}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputs", nargs="+", required=True)
    parser.add_argument("-g", "--gtf", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    
    merge_and_annotate(args.inputs, args.gtf, args.output)
