"""Industry profiles. Reuses the existing scripts/_industry_profiles.py dict
so the Django seed command and the simulator share one source of truth.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._industry_profiles import PROFILES as _RAW_PROFILES  # noqa: E402

PROFILES: dict[str, dict] = _RAW_PROFILES


def get_profile(industry: str) -> dict:
    if industry not in PROFILES:
        raise KeyError(f"Unknown industry: {industry!r}. Known: {sorted(PROFILES)}")
    return clone_profile(PROFILES[industry])


def clone_profile(profile: dict) -> dict:
    return copy.deepcopy(profile)


def normalize_spend_share(profile: dict) -> dict:
    total = sum(c["spend_share"] for c in profile["categories"])
    if total <= 0:
        raise ValueError("All spend_share values are zero")
    for c in profile["categories"]:
        c["spend_share"] = c["spend_share"] / total
    return profile


def normalize_seasonality(profile: dict) -> dict:
    s = profile["seasonality"]
    if len(s) != 12:
        raise ValueError("seasonality must have 12 entries")
    mean = sum(s) / 12
    if mean == 0:
        raise ValueError("seasonality mean is zero")
    profile["seasonality"] = [v / mean for v in s]
    return profile
