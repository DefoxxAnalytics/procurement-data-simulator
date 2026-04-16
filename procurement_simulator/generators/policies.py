from __future__ import annotations

import json

import pandas as pd

from procurement_simulator.generators.base import policy_id


def generate_policies(profile: dict) -> pd.DataFrame:
    rows = []
    for i, spec in enumerate(profile["policies"]):
        rows.append({
            "policy_id": policy_id(i + 1),
            "name": spec["name"],
            "description": spec["description"],
            "rules_json": json.dumps(spec["rules"], sort_keys=True),
            "is_active": True,
        })
    return pd.DataFrame(rows)
