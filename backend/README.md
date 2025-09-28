# Genomics Investigator Agent (GIA)

A fully local system for detecting drift/instability in genomics pipelines, investigating with counterfactual probes, proposing remediation, and validating fixes.

## Features

- **Real-time drift detection** using statistical tests (KS, Chi², PSI, JS divergence)
- **Counterfactual probes** for hypothesis testing (reannotation, realignment, downsampling, etc.)
- **Knowledge graph** tracking pipeline components and dependencies
- **Hypothesis ranking** with confidence scores
- **Automated remediation** with micro-cohort validation
- **Live UI** showing investigation progress
- **Deterministic operation** for reproducible demos

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Genomics tools: `bwa`, `samtools`, `bcftools`
- Homebrew (for macOS)

### Installation

```bash
# Clone and setup
git clone <repo>
cd gia

# Install genomics tools
brew install bwa samtools bcftools

# Setup Python environment
make setup

# Verify data
make seed
```

### Running the Demo

```bash
# Run annotation drift demo
python3 scripts/demo_annotation.py

# Or use the Makefile
make demo-annotation
```

### API Server

```bash
# Start backend
make backend

# Start frontend (in another terminal)
make frontend
```

## Architecture

```
gia/
├── analysis/           # Core analysis modules
│   ├── pipeline.py    # Genomics pipeline wrappers
│   ├── detectors.py   # Drift detection algorithms
│   ├── probes.py      # Counterfactual probes
│   ├── hypotheses.py  # Hypothesis ranking
│   └── kg.py          # Knowledge graph
├── api/               # FastAPI backend
├── ui/                # React frontend
├── data/              # Test data and references
└── runs/              # Pipeline outputs and artifacts
```

## Key Components

### Pipeline Wrappers (`analysis/pipeline.py`)
- `align()` - BWA alignment
- `call_variants()` - BCFtools variant calling  
- `annotate()` - VEP functional annotation
- `predict()` - ML pathogenicity prediction

### Drift Detection (`analysis/detectors.py`)
- Statistical tests: KS, Chi², PSI, JS divergence
- Stage-specific detectors for alignment, calling, annotation, prediction
- Configurable thresholds in `analysis/config.py`

### Counterfactual Probes (`analysis/probes.py`)
- **Reannotation**: Same VCF with different DB versions
- **Realignment**: GRCh37 vs GRCh38 locus alignment
- **Downsampling**: Noise injection and re-calling
- **Caller version**: Different variant caller versions
- **Schema normalization**: Synonym mapping and imputation

### Knowledge Graph (`analysis/kg.py`)
- NetworkX graph of pipeline components
- Vis-network JSON export for UI
- Tracks versions, hashes, and dependencies

## Configuration

### Environment Variables

```bash
# .env
USE_LLM=false                    # Use scripted mode (default)
OPENAI_API_KEY=                  # For LLM mode
LLM_MODEL=gpt-4o-mini           # LLM model
```

### Thresholds (`analysis/config.py`)

```python
thresholds = {
    "alignment": {
        "depth_ks_p": 0.01,
        "softclip_rate_increase": 0.5
    },
    "annotation": {
        "clinvar_chi2_p": 1e-4,
        "consequence_js": 0.1
    }
}
```

## API Endpoints

- `POST /api/run` - Run genomics pipeline
- `POST /api/check_drift` - Detect drift in metrics
- `POST /api/next_probe` - Get next probe to run
- `POST /api/run_probe` - Execute counterfactual probe
- `POST /api/remediate` - Apply remediation patch
- `GET /api/kg/{run_id}` - Get knowledge graph
- `POST /api/summary` - Generate investigation summary

## UI Components

- **Dashboard**: Pipeline status tiles and drift alerts
- **Investigation**: Three-pane view with hypothesis tree, knowledge graph, and evidence tabs
- **Real-time updates**: Live investigation progress

## Demo Scenarios

### Annotation Drift
1. Baseline run with VEP v101
2. Drifted run with VEP v102  
3. Detect ClinVar proportion changes
4. Rank hypotheses (annotation drift #1)
5. Run reannotation probe
6. Propose remediation (pin to v101)
7. Validate on micro-cohort

### Calling Instability
1. Detect variant calling anomalies
2. Run downsampling probe
3. Identify coverage/quality issues
4. Propose parameter adjustments

## Development

### Testing

```bash
# Run all tests
python3 test_e2e.py

# Test individual components
python3 test_pipeline.py
python3 test_detectors.py
```

### Adding New Probes

```python
def new_probe(self, args):
    # Implement probe logic
    return {
        "probe": "new_probe",
        "effect_size": 0.5,
        "p": 0.01,
        "explains_pct": 0.8,
        "artifacts": {}
    }
```

## Troubleshooting

### Simulated Mode
If genomics tools are missing, the system automatically falls back to simulated mode with deterministic results.

### Data Requirements
- Reference genome (FASTA)
- Paired-end reads (FASTQ)
- Annotation databases (VEP cache)

## License

MIT License - see LICENSE file for details.