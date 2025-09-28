#!/usr/bin/env python3
"""
Simple annotation script to replace VEP for testing.
"""
import sys
import gzip
import random

def annotate_vcf(input_vcf, output_vcf, db_version):
    """Simple VCF annotation that adds functional predictions."""
    
    # Set seed for deterministic results
    random.seed(42)
    
    # Read input VCF
    if input_vcf.endswith('.gz'):
        infile = gzip.open(input_vcf, 'rt')
    else:
        infile = open(input_vcf, 'r')
    
    # Write output VCF
    if output_vcf.endswith('.gz'):
        outfile = gzip.open(output_vcf, 'wt')
    else:
        outfile = open(output_vcf, 'w')
    
    # Process VCF
    for line in infile:
        if line.startswith('#'):
            # Header line
            if line.startswith('##INFO'):
                # Add annotation fields
                outfile.write('##INFO=<ID=CSQ,Number=.,Type=String,Description="Consequence annotations">\n')
            outfile.write(line)
        else:
            # Variant line
            fields = line.strip().split('\t')
            if len(fields) >= 8:
                # Parse existing CLNSIG field and add CSQ annotation
                info_field = fields[7]
                
                # Extract existing CLNSIG if present
                existing_clnsig = None
                if 'CLNSIG=' in info_field:
                    clnsig_part = info_field.split('CLNSIG=')[1].split(';')[0]
                    existing_clnsig = clnsig_part
                
                if db_version == 'v101':
                    # Simulate v101 annotations
                    consequence = random.choice(['missense_variant', 'synonymous_variant', 'intron_variant'])
                    if existing_clnsig:
                        # Use existing CLNSIG but convert to our format
                        if 'pathogenic' in existing_clnsig:
                            clinvar = 'pathogenic'
                        elif 'benign' in existing_clnsig:
                            clinvar = 'benign'
                        else:
                            clinvar = 'VUS'
                    else:
                        clinvar = random.choice(['pathogenic', 'benign', 'VUS'])
                else:  # v102
                    # Simulate v102 annotations (more pathogenic)
                    consequence = random.choice(['missense_variant', 'synonymous_variant', 'intron_variant'])
                    if existing_clnsig:
                        # In v102, be more aggressive about pathogenic classification
                        if 'pathogenic' in existing_clnsig or 'likely_pathogenic' in existing_clnsig:
                            clinvar = 'pathogenic'
                        elif 'benign' in existing_clnsig:
                            # 50% chance of reclassifying benign as pathogenic in v102
                            if random.random() < 0.5:
                                clinvar = 'pathogenic'
                            else:
                                clinvar = 'benign'
                        else:
                            clinvar = 'VUS'
                    else:
                        if random.random() < 0.4:  # 40% chance of pathogenic in v102
                            clinvar = 'pathogenic'
                        else:
                            clinvar = random.choice(['benign', 'VUS'])
                
                # Add CSQ annotation to INFO field
                if info_field == '.':
                    info_field = f'CSQ={consequence}|{clinvar}'
                else:
                    info_field += f';CSQ={consequence}|{clinvar}'
                
                fields[7] = info_field
                outfile.write('\t'.join(fields) + '\n')
            else:
                outfile.write(line)
    
    infile.close()
    outfile.close()

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python simple_annotate.py input.vcf output.vcf db_version")
        sys.exit(1)
    
    input_vcf = sys.argv[1]
    output_vcf = sys.argv[2]
    db_version = sys.argv[3]
    
    annotate_vcf(input_vcf, output_vcf, db_version)
    print(f"Annotation completed: {output_vcf}")