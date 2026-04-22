#!/usr/bin/env python3
import sys
import subprocess
import argparse
import os

def convert_read(sequence, method):
    if method == "A2G":
        return sequence.replace('A', 'G')
    elif method == "T2C":
        return sequence.replace('T', 'C')
    return sequence

def stream_fastq(input_file, method):
    """Yields converted FASTQ reads from a file or stdin."""
    # Note: simplified, assuming standard 4-line FASTQ
    if input_file == "-":
        f = sys.stdin
    elif input_file.endswith(".gz"):
        import gzip
        f = gzip.open(input_file, "rt")
    else:
        f = open(input_file, "r")
        
    line_idx = 0
    for line in f:
        if line_idx == 1: # Sequence
            yield convert_read(line.strip(), method) + "\n"
        else:
            yield line
        line_idx = (line_idx + 1) % 4

def run_mapping(fastq_in, index_prefix, threads, method):
    """Pipes converted FASTQ to HISAT2."""
    cmd = [
        "hisat2",
        "-p", str(threads),
        "-x", index_prefix,
        "-U", "-",
        "--no-unal"
    ]
    
    # We'll use a process for hisat2 and feed it from python
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=True)
    
    # In a separate thread or just loop? 
    # For simplicity, we loop and write. For performance, we might need a buffer.
    for line in stream_fastq(fastq_in, method):
        proc.stdin.write(line)
    
    proc.stdin.close()
    return proc

# Actually, doing this in Python might be slower than a simple sed or awk.
# But for GLORI-seq, we need to choose between A2G and T2C.

# THE STRATEGY:
# 1. Pipe umi_tools | cutadapt | tee >(convert A2G | hisat2 -x GA) >(convert T2C | hisat2 -x CT)
# 2. Merge and pick best.
# BUT we want ZERO intermediate files.

if __name__ == "__main__":
    # This script will be a component of the pipe
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["A2G", "T2C"], required=True)
    args = parser.parse_args()
    
    line_idx = 0
    for line in sys.stdin:
        if line_idx == 1:
            sys.stdout.write(convert_read(line.upper(), args.method))
        else:
            sys.stdout.write(line)
        line_idx = (line_idx + 1) % 4
