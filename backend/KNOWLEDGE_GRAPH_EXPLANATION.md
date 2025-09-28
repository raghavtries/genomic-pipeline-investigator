# Knowledge Graph Explanation

## What the Knowledge Graph Shows

The Knowledge Graph visualizes the **complete genomics pipeline** and shows how different components interact with each other. It's like a "family tree" of your genomics analysis.

## Node Types & Colors

### 🧬 **Runs** (Red)
- **What**: Individual pipeline executions
- **Shows**: When the pipeline was run, what sample was processed
- **Example**: "Run 4f7ca68a" - a specific analysis run

### 📚 **Reference Genome** (Teal)
- **What**: The reference genome used for alignment
- **Shows**: Which reference build (e.g., GRCh37), file path, hash
- **Example**: "Reference Genome" - the human reference used

### 🔗 **BWA Aligner** (Blue)
- **What**: The alignment tool that maps reads to reference
- **Shows**: Tool version, configuration
- **Example**: "BWA Aligner" - aligns FASTQ reads to reference

### 🔍 **BCFtools Caller** (Green)
- **What**: The variant calling tool that finds differences
- **Shows**: Tool version, calling parameters
- **Example**: "BCFtools Caller" - finds variants from aligned reads

### 📄 **VCF Files** (Yellow)
- **What**: Variant Call Format files containing the variants
- **Shows**: File hash, path, variant counts
- **Example**: "VCF File" - contains the discovered variants

### 🏷️ **VEP Annotator** (Purple)
- **What**: The annotation tool that adds biological meaning
- **Shows**: Database version, annotation parameters
- **Example**: "VEP Annotator" - adds clinical significance

## Edge Types & Relationships

### **"uses"** (Blue arrows)
- **Meaning**: One component uses another as input
- **Example**: Run → Reference Genome (the run uses the reference)
- **Example**: Annotator → VCF File (annotation uses the VCF)

### **"produced_by"** (Red arrows)
- **Meaning**: One component creates another
- **Example**: Aligner → VCF File (alignment produces the VCF)
- **Example**: Caller → VCF File (variant calling produces the VCF)

## What This Tells Us About Drift

### **Normal Flow**:
```
Run → Reference → Aligner → VCF → Annotator
```

### **When Drift Occurs**:
- **Database Version Changes**: Annotator uses different DB version
- **Tool Updates**: Aligner or Caller gets updated
- **Reference Changes**: Different reference genome used

### **How to Read the Graph**:

1. **Start with a Run** (red node) - this is your analysis
2. **Follow the arrows** to see the pipeline flow
3. **Look for multiple paths** - this shows different versions/configurations
4. **Check node details** - hover/click for specific information

## Example Investigation

If you see:
- **Two Runs** with different timestamps
- **Same Reference** but different **Annotators**
- **Different VCF files** produced

This suggests the **annotation database was updated** between runs, which could explain why you're seeing different results!

## Interactive Features

- **Hover**: See detailed information about each component
- **Click**: Select nodes to highlight relationships
- **Zoom**: Use mouse wheel to zoom in/out
- **Pan**: Click and drag to move around the graph

The knowledge graph helps you understand **exactly what changed** between different pipeline runs, making it easier to identify the root cause of drift!