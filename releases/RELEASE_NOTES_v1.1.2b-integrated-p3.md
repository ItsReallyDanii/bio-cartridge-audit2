# Release Notes — v1.1.2b-integrated-p3

## What this is
A physically bounded Monte Carlo audit engine that estimates:
- water loading on a passive bio-cartridge
- time-integrated aerosol/chemical drift capture from data-center exhaust

with unit-safe ledgers and hard saturation limits.

## What this is not
- Not CFD
- Not field-calibrated per-site chemistry by default
- Not geometry-validated beyond hypothesis-grade overlays

## Inputs
- Environmental priors: T_air, RH, v_air, C_drift_air
- Collector params: A_face, A_effective, M_max
- Chemistry: f_chem_i
- Optional profile overlay from `research/geometry/prior_ranges.yaml`
- Optional CLI overrides via `--set key=mean,std,low,high`

## Outputs
- Probabilistic breakpoint report
- Final ledger summary at t=7 days
- Provenance header (profile/source/evidence/status)

## Repro commands
```bash
python -m pytest -q
python src/baseline_v1_1_2b.py --no-plot
python src/baseline_v1_1_2b.py --profile stenocara_profile --no-plot
python src/baseline_v1_1_2b.py --profile sphagnum_profile --no-plot
python src/baseline_v1_1_2b.py --profile cactaceae_profile --no-plot

## 7) Git freeze + tag
```powershell
git status
git add .
git commit -m "chore(release): lock v1.1.2b-integrated-p3"
git tag v1.1.2b-integrated-p3
git push origin main
git push origin v1.1.2b-integrated-p3
