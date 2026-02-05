# Bio-Cartridge Audit

## Release
`v1.1.2b-integrated-p3`

## Purpose
Auditor-grade Monte Carlo baseline for bio-cartridge capture auditing, with strict separation between:
- **Immutable baseline engine** (`src/baseline_v1_1_2b.py`)
- **Profile overlay loader** (`src/profile_loader.py`)
- **Research-only geometry priors** (`research/geometry/`)

## Modes
- **Mode A (Baseline):** no profile selected; release-of-record behavior.
- **Mode B (Overlay):** `--profile <name>` loads geometry priors with provenance.
- **CLI what-if overrides:** `--set key=mean,std,low,high` (validated against allowlist).

## Quick Start
```bash
pip install -r requirements.txt
python src/baseline_v1_1_2b.py
pytest tests/test_sanity.py
```

## Example Profile Run
```bash
python src/baseline_v1_1_2b.py --profile stenocara_profile
```

## Example Override
```bash
python src/baseline_v1_1_2b.py --set eta_mean=0.3,0.05,0.1,0.5
```

## Current Status
Current status: Phase 4 benchmark complete; awaiting default-profile selection for operational runs.
