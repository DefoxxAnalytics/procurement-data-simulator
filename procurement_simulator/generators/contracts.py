from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import contract_id


def generate_contracts(
    org_slug: str,
    suppliers_df: pd.DataFrame,
    categories_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    n_contracts: int,
    today,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (contracts_df, contract_categories_df)."""
    spend = (
        transactions_df.groupby("supplier_id")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    top_ids = spend.head(n_contracts).index.tolist()
    id_to_name = dict(zip(suppliers_df["supplier_id"], suppliers_df["name"]))
    cat_ids = categories_df["category_id"].tolist()

    rows: list[dict] = []
    link_rows: list[dict] = []
    for i, sid in enumerate(top_ids):
        roll = float(rng.random())
        if roll < 0.70:
            status = "active"
            start = today - timedelta(days=int(rng.integers(90, 600)))
            end = today + timedelta(days=int(rng.integers(30, 540)))
        elif roll < 0.85:
            status = "expiring"
            start = today - timedelta(days=int(rng.integers(300, 700)))
            end = today + timedelta(days=int(rng.integers(5, 60)))
        else:
            status = "expired"
            start = today - timedelta(days=int(rng.integers(400, 900)))
            end = today - timedelta(days=int(rng.integers(10, 120)))

        supplier_spend = float(spend.get(sid, 0.0))
        annual_value = round(supplier_spend * float(rng.uniform(0.6, 1.1)) / 2, 2) if supplier_spend else 50000.0
        years = max((end - start).days / 365.0, 0.25)
        total_value = round(annual_value * years, 2)

        cid = contract_id(org_slug, start.year, i + 1)
        name = id_to_name.get(sid, sid)
        rows.append({
            "contract_id": cid,
            "supplier_id": sid,
            "contract_number": cid,
            "title": f"{name[:60]} Master Services Agreement",
            "description": f"Multi-year MSA covering services with {name[:80]}",
            "total_value": total_value,
            "annual_value": annual_value,
            "start_date": start,
            "end_date": end,
            "renewal_notice_days": int(rng.choice([30, 60, 90, 120])),
            "status": status,
            "auto_renew": bool(rng.random() < 0.35),
        })
        n_cats = int(rng.integers(1, 4))
        picks = rng.choice(cat_ids, size=min(n_cats, len(cat_ids)), replace=False)
        for c in picks.tolist():
            link_rows.append({"contract_id": cid, "category_id": c})

    return pd.DataFrame(rows), pd.DataFrame(link_rows, columns=["contract_id", "category_id"])
