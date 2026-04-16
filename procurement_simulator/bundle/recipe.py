from __future__ import annotations

from typing import Any

import yaml

GENERATOR_VERSION = "0.1.0"


def build_recipe(
    industry: str,
    config: dict,
    profile: dict,
    baseline_profile: dict,
    scenarios: list[dict],
) -> dict[str, Any]:
    overrides = _diff_profile(baseline_profile, profile)
    return {
        "generator_version": GENERATOR_VERSION,
        "industry": industry,
        "config": config,
        "profile_overrides": overrides,
        "scenarios": scenarios,
    }


def dump_recipe(recipe: dict) -> str:
    return yaml.safe_dump(recipe, sort_keys=False, default_flow_style=False)


def load_recipe(text: str) -> dict:
    return yaml.safe_load(text)


def _diff_profile(baseline: dict, current: dict) -> dict:
    """Returns only keys whose values differ from the baseline.
    Shallow diff for top-level scalars, deep diff for categories list (by name)
    and seasonality list.
    """
    overrides: dict[str, Any] = {}

    for key in ("seasonality", "cost_center_prefix", "name"):
        if key in baseline and key in current and baseline[key] != current[key]:
            overrides[key] = current[key]

    if "categories" in baseline and "categories" in current:
        base_by_name = {c["name"]: c for c in baseline["categories"]}
        cat_overrides: list[dict] = []
        for c in current["categories"]:
            b = base_by_name.get(c["name"])
            if not b:
                cat_overrides.append(c)
                continue
            delta: dict = {}
            for k in ("spend_share", "amount_mu", "amount_sigma"):
                if b.get(k) != c.get(k):
                    delta[k] = c.get(k)
            if delta:
                delta["name"] = c["name"]
                cat_overrides.append(delta)
        if cat_overrides:
            overrides["categories"] = cat_overrides

    return overrides


def apply_overrides(baseline: dict, overrides: dict) -> dict:
    from copy import deepcopy
    out = deepcopy(baseline)
    for key, value in overrides.items():
        if key == "categories":
            base_by_name = {c["name"]: c for c in out["categories"]}
            for delta in value:
                name = delta.get("name")
                if name in base_by_name:
                    base_by_name[name].update({k: v for k, v in delta.items() if k != "name"})
                else:
                    out["categories"].append(delta)
        else:
            out[key] = value
    return out
