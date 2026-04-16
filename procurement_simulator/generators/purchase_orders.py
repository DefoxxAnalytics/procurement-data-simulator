from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import po_id

_STATUSES = [
    "fully_received", "partially_received", "acknowledged", "sent_to_supplier",
    "approved", "closed", "pending_approval", "draft", "cancelled",
]
_STATUS_P = np.array([0.35, 0.15, 0.15, 0.10, 0.10, 0.05, 0.05, 0.03, 0.02])
_AMENDMENT_COUNTS = np.array([0, 1, 2, 3])
_AMENDMENT_P = np.array([0.75, 0.17, 0.06, 0.02])


def generate_pos(
    org_slug: str,
    suppliers_df: pd.DataFrame,
    categories_df: pd.DataFrame,
    contracts_df: pd.DataFrame,
    prs_df: pd.DataFrame,
    n_pos: int,
    today,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (pos_df, updated_prs_df)."""
    contracts_by_sup: dict[str, list[str]] = {}
    if not contracts_df.empty:
        for sid, cid in zip(contracts_df["supplier_id"], contracts_df["contract_id"]):
            contracts_by_sup.setdefault(sid, []).append(cid)
    contract_supplier_ids = list(contracts_by_sup.keys())

    convertible = prs_df[prs_df["status"].isin(["approved", "converted_to_po"])].copy()
    convertible = convertible.sample(frac=1, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)
    pr_pool_size = int(n_pos * 0.7)
    pr_pool = convertible.head(pr_pool_size)

    sup_ids = suppliers_df["supplier_id"].to_numpy()
    cat_ids = categories_df["category_id"].to_numpy()

    statuses = rng.choice(_STATUSES, size=n_pos, p=_STATUS_P / _STATUS_P.sum())
    amendment_counts = rng.choice(_AMENDMENT_COUNTS, size=n_pos, p=_AMENDMENT_P / _AMENDMENT_P.sum())

    rows = []
    converted_pr_ids: list[str] = []

    for i in range(n_pos):
        if i < len(pr_pool):
            pr = pr_pool.iloc[i]
            supplier = pr["supplier_suggested_id"]
            category = pr["category_id"]
            created = pr["approval_date"] if pd.notna(pr["approval_date"]) else pr["created_date"]
            base_amount = float(pr["estimated_amount"])
            requisition = pr["pr_id"]
            converted_pr_ids.append(pr["pr_id"])
        else:
            if contract_supplier_ids and float(rng.random()) < 0.75:
                supplier = contract_supplier_ids[int(rng.integers(0, len(contract_supplier_ids)))]
            else:
                supplier = str(sup_ids[int(rng.integers(0, min(500, len(sup_ids))))])
            category = str(cat_ids[int(rng.integers(0, len(cat_ids)))])
            created = today - timedelta(days=int(rng.integers(1, 181)))
            base_amount = round(float(rng.uniform(1000, 80000)), 2)
            requisition = None

        variance = float(rng.uniform(0.95, 1.08))
        total = round(base_amount * variance, 2)
        tax = round(total * 0.08, 2)
        freight = round(float(rng.uniform(0, 500)), 2)

        contract = None
        pool = contracts_by_sup.get(supplier, [])
        if pool and float(rng.random()) < 0.80:
            contract = pool[int(rng.integers(0, len(pool)))]

        status = statuses[i]
        approval = created + timedelta(days=int(rng.integers(0, 4))) if status not in {"draft", "pending_approval"} else None
        sent = None
        if approval is not None and status in {"sent_to_supplier", "acknowledged", "partially_received", "fully_received", "closed"}:
            sent = approval + timedelta(days=int(rng.integers(0, 3)))
        required = created + timedelta(days=int(rng.integers(14, 61)))
        promised = required + timedelta(days=int(rng.integers(-5, 11))) if sent is not None else None

        amendment_count = int(amendment_counts[i])
        original_amount = round(total / float(rng.uniform(1.0, 1.15)), 2) if amendment_count > 0 else None

        rows.append({
            "po_id": po_id(org_slug, created.year, i + 1),
            "po_number": po_id(org_slug, created.year, i + 1),
            "supplier_id": supplier,
            "category_id": category,
            "total_amount": total,
            "tax_amount": tax,
            "freight_amount": freight,
            "contract_id": contract,
            "is_contract_backed": contract is not None,
            "status": status,
            "created_date": created,
            "approval_date": approval,
            "sent_date": sent,
            "required_date": required,
            "promised_date": promised,
            "original_amount": original_amount,
            "amendment_count": amendment_count,
            "pr_id": requisition,
        })

    pos_df = pd.DataFrame(rows)

    if converted_pr_ids:
        mask = prs_df["pr_id"].isin(converted_pr_ids) & (prs_df["status"] == "approved")
        prs_df = prs_df.copy()
        prs_df.loc[mask, "status"] = "converted_to_po"

    return pos_df, prs_df
