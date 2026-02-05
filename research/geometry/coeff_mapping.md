# Geometry to Coefficient Mapping (v0.2)

- Reynolds: `Re = rho * v * L / mu`
- Stokes: `Stk = rho_p * d_p^2 * v / (18 * mu * L)`

Interpretation:
- Higher `Re_local` can increase effective mass transfer (`k_w_eff`).
- `Stk << 1`: low inertial capture.
- `Stk ~ 1`: transition window.
- `Stk >> 1`: strong inertial impaction.
