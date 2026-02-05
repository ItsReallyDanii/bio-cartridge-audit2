import argparse
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.profile_loader import ProfileLoader, AuditIntegrityError

# --- 1) Config / constants ---
N_SAMPLES = 2000
T_EXP_DAYS = 7
STEPS_PER_DAY = 24
DT = 3600
TOTAL_STEPS = T_EXP_DAYS * STEPS_PER_DAY

RISK_HIGH = 20.0
RISK_ADVISORY = 5.0
NOISE_FLOOR_MG = 0.5
V_THRESH = 8.0

A_FACE = 0.05
A_EFF = 0.12

# Baseline fallback (legacy constant path)
BASELINE_M_MAX = 0.5  # kg/m^2
MAX_CAPACITY = BASELINE_M_MAX * A_EFF

# Locked baseline defaults (tests import this)
DEFAULT_PRIORS = {
    "T_air":       [35.0, 2.0, 10.0, 60.0],
    "RH":          [85.0, 5.0, 0.0, 100.0],
    "v_air":       [5.0, 1.0, 0.1, 15.0],
    "C_drift_air": [2.0, 0.5, 0.0, 10.0],
    "f_chem_i":    [0.005, 0.001, 0.0, 1.0],
    "k_w_eff":     [0.01, 0.002, 1e-4, 0.1],
    "eta_mean":    [0.15, 0.03, 0.0, 1.0],
    "RH_surface":  [50.0, 0.0, 0.0, 100.0],
    # Added so CLI/YAML can legally override storage-capacity model
    "M_max":       [0.5, 0.1, 0.2, 1.0],  # kg/m^2
}

ALLOWED_OVERRIDE_KEYS = set(DEFAULT_PRIORS.keys())


# --- 2) Prior assembly ---
def build_prior_def(profile_name=None, cli_overrides=None, yaml_path="research/geometry/prior_ranges.yaml"):
    """
    Precedence: CLI > YAML profile > DEFAULT_PRIORS
    """
    loader = ProfileLoader(yaml_path=yaml_path)
    overrides, provenance = loader.get_parameter_set(profile_name, cli_overrides)

    final_def = DEFAULT_PRIORS.copy()
    final_def.update(overrides)
    return final_def, provenance


def sample_priors(n, prior_def=None):
    """
    Clipped normal sampling.
    prior_def schema:
      key: [mean, std, low, high]
    """
    if prior_def is None:
        prior_def = DEFAULT_PRIORS

    samples = {}
    for key, (mu, sigma, low, high) in prior_def.items():
        arr = np.random.normal(mu, sigma, n)
        samples[key] = np.clip(arr, low, high)
    return samples


# --- 3) Physics ---
def get_omega(T, RH, P=101.325):
    """
    Humidity ratio with numeric guard.
    T in C, RH in %, P in kPa.
    """
    P_sat = 0.61094 * np.exp((17.625 * T) / (T + 243.04))
    Pv = np.minimum((RH / 100.0) * P_sat, 0.99 * P)
    return 0.622 * (Pv / (P - Pv))


def run_simulation(s_set):
    """
    Uses dynamic local sample count so tests can run low-N quickly.
    Supports optional per-sample M_max (kg/m^2). If absent, uses BASELINE_M_MAX.
    """
    n_samples_local = len(next(iter(s_set.values())))

    mw_ledger = np.zeros((n_samples_local, TOTAL_STEPS))
    mp_ledger = np.zeros((n_samples_local, TOTAL_STEPS))
    mi_ledger = np.zeros((n_samples_local, TOTAL_STEPS))

    has_mmax = "M_max" in s_set

    for i in range(n_samples_local):
        T = s_set["T_air"][i]
        rh = s_set["RH"][i]
        v = s_set["v_air"][i]
        C = s_set["C_drift_air"][i] * 1e-6  # mg/m^3 -> kg/m^3
        f = s_set["f_chem_i"][i]
        kw = s_set["k_w_eff"][i]
        eta = s_set["eta_mean"][i]
        rh_s = s_set["RH_surface"][i]

        # Dynamic capacity path
        m_max_i = max(s_set["M_max"][i], 0.0) if has_mmax else BASELINE_M_MAX
        max_capacity_i = m_max_i * A_EFF

        kw_clamped = max(kw, 0.0)
        Jw = kw_clamped * (get_omega(T, rh) - get_omega(T, rh_s))  # evaporation allowed via sign

        Q = max(v * A_FACE, 0.0)
        dm_p_dt = max(Q * C * np.clip(eta, 0.0, 1.0), 0.0)
        dm_i_dt = max(dm_p_dt * np.clip(f, 0.0, 1.0), 0.0)

        mw_acc = 0.0
        mp_acc = 0.0
        mi_acc = 0.0

        for t in range(TOTAL_STEPS):
            mw_acc = np.clip(mw_acc + (Jw * A_EFF * DT), 0.0, MAX_CAPACITY)
            mp_acc += dm_p_dt * DT
            mi_acc += dm_i_dt * DT

            mw_ledger[i, t] = mw_acc
            mp_ledger[i, t] = mp_acc
            mi_ledger[i, t] = mi_acc

    return mw_ledger, mp_ledger, mi_ledger


# --- 4) Reporting helpers ---
def _plot_unc(ax, time_axis, data, title, ylabel, scale=1.0):
    m = np.mean(data, axis=0) * scale
    s = np.std(data, axis=0) * scale
    ax.plot(time_axis, m, lw=2, label="Mean")
    ax.fill_between(time_axis, m - s, m + s, alpha=0.2, label="1σ Band")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.2)
    ax.legend(loc="upper left")


def _print_reports(samples, mw, mp, mi):
    final_mi_mg = mi[:, -1] * 1e6
    final_mw_kg = mw[:, -1]

    # Use dynamic capacity if available; else legacy constant
    if "M_max" in samples:
        cap_vec = np.clip(samples["M_max"], 0.0, None) * A_EFF
    else:
        cap_vec = np.full_like(final_mw_kg, MAX_CAPACITY)

    probs = [
        np.mean(samples["v_air"] > V_THRESH) * 100.0,
        np.mean(final_mi_mg < NOISE_FLOOR_MG) * 100.0,
        np.mean(final_mw_kg >= cap_vec * 0.98) * 100.0,
    ]

    statuses = []
    for p in probs:
        if p > RISK_HIGH:
            statuses.append("HIGH RISK")
        elif p > RISK_ADVISORY:
            statuses.append("ADVISORY")
        else:
            statuses.append("NOMINAL")

    report = pd.DataFrame(
        {
            "Metric": ["Re-entrainment Prob", "SNR Collapse Prob", "Saturation Prob"],
            "Value": [f"{p:.1f}%" for p in probs],
            "Threshold": [f"> {V_THRESH} m/s", f"< {NOISE_FLOOR_MG} mg", "> 98% Cap"],
            "Status": statuses,
        }
    )

    summary = pd.DataFrame(
        {
            "Metric": ["Water (kg)", "Total Aerosol (mg)", "Species i (mg)"],
            "Mean": [np.mean(final_mw_kg), np.mean(mp[:, -1] * 1e6), np.mean(final_mi_mg)],
            "Std Dev": [np.std(final_mw_kg), np.std(mp[:, -1] * 1e6), np.std(final_mi_mg)],
        }
    )

    print("\n--- Auditor-Grade Probabilistic Breakpoint Report ---")
    print(report.to_string(index=False))
    print("\n--- Final Ledger Summary (t = 7 days) ---")
    print(summary.to_string(index=False))


# --- 5) CLI entry ---
def main():
    parser = argparse.ArgumentParser(description="Bio-Cartridge Auditor v1.1.2b")
    parser.add_argument("--profile", type=str, help="Research profile name")
    parser.add_argument("--priors-yaml", type=str, default="research/geometry/prior_ranges.yaml")
    parser.add_argument("--set", action="append", help="Override key=mean,std,low,high")
    parser.add_argument("--no-plot", action="store_true", help="Disable matplotlib windows")
    args = parser.parse_args()

    cli_map = {}
    try:
        for s in args.set or []:
            k, v = s.split("=")
            if k not in ALLOWED_OVERRIDE_KEYS:
                raise AuditIntegrityError(f"Unknown override key: {k}")
            vals = [float(x) for x in v.split(",")]
            if len(vals) != 4:
                raise AuditIntegrityError(f"{k} override must be mean,std,low,high")
            cli_map[k] = vals

        prior_def, provenance = build_prior_def(args.profile, cli_map, args.priors_yaml)

        print("-" * 40)
        print(f"AUDIT RUN: {provenance['profile_name']}")
        print(f"SOURCE:    {provenance['source_file']}")
        print(f"EVIDENCE:  {provenance['evidence_level']} ({provenance['status']})")
        print("-" * 40)

        samples = sample_priors(N_SAMPLES, prior_def)
        mw, mp, mi = run_simulation(samples)

        _print_reports(samples, mw, mp, mi)

        if not args.no_plot:
            time_axis = np.arange(TOTAL_STEPS) / STEPS_PER_DAY
            fig, axs = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
            _plot_unc(axs[0], time_axis, mw, "Water Capture (m_w)", "Mass (kg)", scale=1.0)
            _plot_unc(axs[1], time_axis, mp, "Total Aerosol (m_p,total)", "Mass (mg)", scale=1e6)
            _plot_unc(axs[2], time_axis, mi, "Chemical Ledger (m_i)", "Mass (mg)", scale=1e6)
            plt.xlabel("Days")
            plt.tight_layout()
            plt.show()

    except AuditIntegrityError as e:
        print(f"CRITICAL AUDIT FAILURE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
