# Bio-Cartridge Profile Schema (v1.0)

## Allowed Keys
- `status` (required)
- `evidence_level` (required)
- `k_w_eff` (optional quad tuple)
- `eta_mean` (optional quad tuple)
- `M_max` (optional quad tuple)
- `RH_surface` (optional quad tuple)

## Quad Tuple
`[mean, std, low, high]`

## Validation
- `low <= mean <= high`
- `std >= 0`
- `k_w_eff >= 0`
- `0 <= eta_mean <= 1`
- `M_max >= 0`
- `0 <= RH_surface <= 100`

## Precedence
CLI overrides > YAML profile > baseline defaults
