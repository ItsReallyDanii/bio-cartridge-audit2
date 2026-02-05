# Phase 3 Profile Integration Plan

## Overlay Pattern
1. Start from immutable baseline defaults.
2. Optionally apply selected YAML profile block.
3. Apply CLI overrides last.

## Mandatory Provenance
- `profile_name`
- `evidence_level`
- `status`
- `source_file`

## Auditor Gates
- Mode A hash-consistent with locked baseline.
- Mode B only on explicit selector.
- Strict schema validation and unknown-key rejection.
- No cross-run/global state leakage.
