import os
import yaml


class AuditIntegrityError(Exception):
    """Raised when profile validation fails or invariants are breached."""
    pass


class ProfileLoader:
    ALLOWED_KEYS = {"status", "evidence_level", "k_w_eff", "eta_mean", "M_max", "RH_surface"}
    REQUIRED_METADATA = {"status", "evidence_level"}

    def __init__(self, yaml_path="research/geometry/prior_ranges.yaml"):
        self.yaml_path = yaml_path
        self.profiles = self._load_yaml()

    def _load_yaml(self):
        if not os.path.exists(self.yaml_path):
            return {}
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}

    def validate_profile(self, name, data):
        # allowlist
        for key in data.keys():
            if key not in self.ALLOWED_KEYS:
                raise AuditIntegrityError(f"Rejected unknown key '{key}' in profile '{name}'")

        # metadata required
        for req in self.REQUIRED_METADATA:
            if req not in data:
                raise AuditIntegrityError(f"Missing required metadata '{req}' in profile '{name}'")

        # tuple + invariants + domains
        for key, val in data.items():
            if key in self.REQUIRED_METADATA:
                continue

            if not isinstance(val, list) or len(val) != 4 or not all(isinstance(x, (int, float)) for x in val):
                raise AuditIntegrityError(f"Key '{key}' in '{name}' must be [mean, std, low, high] numeric list")

            mean, std, low, high = val
            if std < 0 or not (low <= mean <= high):
                raise AuditIntegrityError(f"Invariant breach in '{name}' for '{key}': {val}")

            if key == "eta_mean":
                if not (0 <= low <= high <= 1 and 0 <= mean <= 1):
                    raise AuditIntegrityError("Domain breach: eta_mean must be in [0,1]")
            elif key == "RH_surface":
                if not (0 <= low <= high <= 100 and 0 <= mean <= 100):
                    raise AuditIntegrityError("Domain breach: RH_surface must be in [0,100]")
            elif key in ("k_w_eff", "M_max"):
                if low < 0 or mean < 0 or high < 0:
                    raise AuditIntegrityError(f"Domain breach: {key} must be >= 0")

    def get_parameter_set(self, profile_name=None, cli_overrides=None):
        provenance = {
            "profile_name": "baseline",
            "evidence_level": "release-of-record",
            "status": "immutable",
            "source_file": "src/baseline_v1_1_2b.py",
        }

        final_priors = {}

        if profile_name is not None:
            if profile_name not in self.profiles:
                raise AuditIntegrityError(f"Profile '{profile_name}' not found in {self.yaml_path}")

            profile_data = self.profiles[profile_name]
            self.validate_profile(profile_name, profile_data)

            provenance.update(
                {
                    "profile_name": profile_name,
                    "evidence_level": profile_data["evidence_level"],
                    "status": profile_data["status"],
                    "source_file": self.yaml_path,
                }
            )

            for k, v in profile_data.items():
                if k not in self.REQUIRED_METADATA:
                    final_priors[k] = v

        if cli_overrides:
            final_priors.update(cli_overrides)

        return final_priors, provenance
