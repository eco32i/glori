import pandas as pd
import numpy as np
import sys

def compare(modern_csv, ground_truth_csv):
    print(f"Comparing {modern_csv} to {ground_truth_csv}...")
    
    # Simple load
    m = pd.read_csv(modern_csv, index_col=0, low_memory=False)
    # The first row of data is actually level 2 of the header in modern
    # Let's just fix columns manually
    
    gt = pd.read_csv(ground_truth_csv, index_col=0, low_memory=False, skiprows=[0])
    
    common = m.index.intersection(gt.index)
    print(f"Common IDs: {len(common)}")
    
    # Modern columns are like 'ratio', 'ratio.1' etc because of multi-index CSV load
    # Let's find columns containing 'ratio' or 'coverage'
    
    m_ratio_cols = [c for c in m.columns if 'ratio' in c]
    gt_ratio_cols = [c for c in gt.columns if 'm6A level' in c]
    
    print(f"Modern ratio cols: {m_ratio_cols}")
    print(f"GT ratio cols: {gt_ratio_cols}")
    
    if len(common) > 0:
        # Just compare the first one found
        m_vals = pd.to_numeric(m.loc[common, m_ratio_cols[0]], errors='coerce')
        g_vals = pd.to_numeric(gt.loc[common, gt_ratio_cols[0]], errors='coerce')
        
        corr = m_vals.corr(g_vals)
        print(f"Correlation: {corr:.4f}")

if __name__ == "__main__":
    compare(sys.argv[1], sys.argv[2])
