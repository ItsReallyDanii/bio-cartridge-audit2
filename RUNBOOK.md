# Bio-Cartridge Runbook

## 1. Environment Setup
Python 3.9+ is required. Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Execution
Run the baseline simulator directly to generate plots and reports:

```bash
python src/baseline_v1_1_2b.py
```

## 3. Testing
Execute the sanity test suite to verify model invariants (non-negativity, clamping, monotonicity):

```bash
export PYTHONPATH=$PYTHONPATH:.
pytest tests/test_sanity.py
```

## 4. Data Artifacts (v0 Status)
- `default_priors.yaml`: Defines initial Auditor Priors. Currently documentation-only; future versions may support direct ingestion.
- `template_log.csv`: Field-data schema. Not currently consumed by the simulator.
