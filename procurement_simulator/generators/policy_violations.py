from __future__ import annotations

import json

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import violation_id


_VIOLATION_TYPES = ["amount_exceeded", "no_contract", "non_preferred_supplier", "approval_missing"]
_VIOLATION_TYPE_WEIGHTS = np.array([0.4, 0.3, 0.2, 0.1])
_SEVERITIES = ["critical", "high", "medium", "low"]
_SEVERITY_WEIGHTS = np.array([0.10, 0.25, 0.45, 0.20])


def generate_policy_violations(
    transactions_df: pd.DataFrame,
    policies_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    n_violations: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    if policies_df.empty or transactions_df.empty:
        return pd.DataFrame(columns=[
            "violation_id", "transaction_id", "policy_id", "violation_type",
            "severity", "details_json", "is_resolved",
        ])

    high_value = transactions_df[transactions_df["amount"] > 5000].copy()
    if high_value.empty:
        return pd.DataFrame(columns=[
            "violation_id", "transaction_id", "policy_id", "violation_type",
            "severity", "details_json", "is_resolved",
        ])
    high_value = high_value.sort_values("amount", ascending=False).head(n_violations * 3)
    sample_n = min(n_violations, len(high_value))
    sample = high_value.sample(n=sample_n, random_state=int(rng.integers(0, 2**31 - 1)))

    sup_map = dict(zip(suppliers_df["supplier_id"], suppliers_df["name"]))
    policy_ids = policies_df["policy_id"].to_numpy()

    v_types = rng.choice(_VIOLATION_TYPES, size=sample_n, p=_VIOLATION_TYPE_WEIGHTS / _VIOLATION_TYPE_WEIGHTS.sum())
    severities = rng.choice(_SEVERITIES, size=sample_n, p=_SEVERITY_WEIGHTS / _SEVERITY_WEIGHTS.sum())
    chosen_policies = rng.choice(policy_ids, size=sample_n)
    resolved = rng.random(sample_n) < 0.25

    rows = []
    for i, (_, t) in enumerate(sample.iterrows()):
        rows.append({
            "violation_id": violation_id(i + 1),
            "transaction_id": t["transaction_id"],
            "policy_id": chosen_policies[i],
            "violation_type": v_types[i],
            "severity": severities[i],
            "details_json": json.dumps({
                "amount": float(t["amount"]),
                "supplier": sup_map.get(t["supplier_id"], t["supplier_id"]),
                "flagged_at": str(t["date"]),
            }, sort_keys=True),
            "is_resolved": bool(resolved[i]),
        })
    return pd.DataFrame(rows)
