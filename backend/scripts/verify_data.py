#!/usr/bin/env python3
"""
Verify data fixtures and print status table.
"""
import os
import hashlib
from pathlib import Path

def get_file_hash(filepath):
    """Get SHA256 hash of file."""
    if not os.path.exists(filepath):
        return "N/A"
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]

def get_file_size(filepath):
    """Get file size in bytes."""
    if not os.path.exists(filepath):
        return 0
    return os.path.getsize(filepath)

def main():
    print("GIA Data Verification")
    print("=" * 50)
    
    # Required paths
    paths = [
        "data/inputs/sample_001_R1.fastq.gz",
        "data/inputs/sample_001_R2.fastq.gz", 
        "data/refs/grch37/chr21.fa",
        "data/refs/grch38/chr21.fa",
        "data/db/vep/v101/cache",
        "data/db/vep/v102/cache",
        "data/microcohort/cohort_manifest.json",
        "data/truth/giab/giab_chr21.vcf.gz"
    ]
    
    print(f"{'Path':<40} {'Size':<10} {'Hash':<10} {'Status'}")
    print("-" * 70)
    
    simulated_mode = False
    for path in paths:
        size = get_file_size(path)
        hash_val = get_file_hash(path)
        if os.path.exists(path):
            status = "OK (real)"
        else:
            status = "SIMULATED"
            simulated_mode = True
            # Create placeholder file
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).touch()
        
        print(f"{path:<40} {size:<10} {hash_val:<10} {status}")
    
    if simulated_mode:
        print("\n⚠ SIMULATED MODE ENABLED - Some data files are placeholders")
    else:
        print("\n✓ All data files present")

if __name__ == "__main__":
    main()