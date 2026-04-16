from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import pr_id

_STATUSES = ["approved", "converted_to_po", "pending_approval", "rejected", "draft", "cancelled"]
_STATUS_P = np.array([0.55, 0.20, 0.10, 0.08, 0.05, 0.02])
_PRIORITIES = ["low", "normal", "high", "urgent"]
_PRIORITY_P = np.array([0.15, 0.60, 0.20, 0.05])


def generate_prs(
    org_slug: str,
    profile: dict,
    suppliers_df: pd.DataFrame,
    categories_df: pd.DataFrame,
    n_prs: int,
    today,
    rng: np.random.Generator,
) -> pd.DataFrame:
    departments = profile["departments"]
    cc_prefix = profile["cost_center_prefix"]
    cost_centers = [f"{cc_prefix}-{n:04d}" for n in range(1000, 1030)]

    sup_ids = suppliers_df["supplier_id"].to_numpy()
    weights = np.ones(len(sup_ids))
    weights[:80] *= 5
    if len(sup_ids) > 80:
        weights[80:200] *= 2
    weights = weights / weights.sum()

    cat_ids = categories_df["category_id"].to_numpy()

    statuses = rng.choice(_STATUSES, size=n_prs, p=_STATUS_P / _STATUS_P.sum())
    priorities = rng.choice(_PRIORITIES, size=n_prs, p=_PRIORITY_P / _PRIORITY_P.sum())
    amounts = np.round(rng.uniform(500, 50000, size=n_prs), 2)
    days_back = rng.integers(1, 211, size=n_prs)
    suppliers = rng.choice(sup_ids, size=n_prs, p=weights)
    categories = rng.choice(cat_ids, size=n_prs)

    rows = []
    for i in range(n_prs):
        created = today - timedelta(days=int(days_back[i]))
        status = statuses[i]
        submitted = created + timedelta(days=int(rng.integers(0, 3))) if status != "draft" else None
        approved = submitted + timedelta(days=int(rng.integers(0, 8))) if submitted is not None and status in {"approved", "converted_to_po"} else None
        rejected = submitted + timedelta(days=int(rng.integers(1, 6))) if submitted is not None and status == "rejected" else None

        rows.append({
            "pr_id": pr_id(org_slug, created.year, i + 1),
            "pr_number": pr_id(org_slug, created.year, i + 1),
            "department": departments[int(rng.integers(0, len(departments)))],
            "cost_center": cost_centers[int(rng.integers(0, len(cost_centers)))],
            "supplier_suggested_id": suppliers[i],
            "category_id": categories[i],
            "description": f"Purchase request #{i + 1} for operational needs",
            "estimated_amount": float(amounts[i]),
            "status": status,
            "priority": priorities[i],
            "created_date": created,
            "submitted_date": submitted,
            "approval_date": approved,
            "rejection_date": rejected,
            "rejection_reason": "Budget exceeded for period" if rejected is not None else "",
        })
    return pd.DataFrame(rows)
