from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import gr_id

_QTY_CHOICES = np.array([1, 5, 10, 25, 50, 100, 250])


def generate_grs(
    org_slug: str,
    pos_df: pd.DataFrame,
    n_grs: int,
    today,
    rng: np.random.Generator,
) -> pd.DataFrame:
    receivable = pos_df[pos_df["status"].isin(["partially_received", "fully_received", "acknowledged", "closed"])].copy()
    if receivable.empty:
        return pd.DataFrame()
    receivable = receivable.sample(frac=1, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)
    target = receivable.head(n_grs)

    rows = []
    for i in range(len(target)):
        po = target.iloc[i]
        base_date = po["sent_date"] if pd.notna(po["sent_date"]) else po["approval_date"] if pd.notna(po["approval_date"]) else po["created_date"]
        received = base_date + timedelta(days=int(rng.integers(7, 46)))
        if received > today:
            received = today - timedelta(days=int(rng.integers(0, 8)))

        qty_ordered = float(_QTY_CHOICES[int(rng.integers(0, len(_QTY_CHOICES)))])
        if po["status"] == "partially_received":
            qty_received = round(qty_ordered * float(rng.uniform(0.4, 0.85)), 2)
        else:
            qty_received = round(qty_ordered * float(rng.uniform(0.95, 1.02)), 2)

        accept_roll = float(rng.random())
        if accept_roll < 0.80:
            qty_accepted = qty_received
            status = "accepted"
        elif accept_roll < 0.92:
            qty_accepted = round(qty_received * 0.90, 2)
            status = "partial_accept"
        elif accept_roll < 0.97:
            qty_accepted = 0.0
            status = "rejected"
        else:
            qty_accepted = None
            status = "pending"

        amount_received = round(float(po["total_amount"]) * (qty_received / qty_ordered), 2)

        rows.append({
            "gr_id": gr_id(org_slug, received.year, i + 1),
            "gr_number": gr_id(org_slug, received.year, i + 1),
            "po_id": po["po_id"],
            "received_date": received,
            "quantity_ordered": qty_ordered,
            "quantity_received": qty_received,
            "quantity_accepted": qty_accepted,
            "amount_received": amount_received,
            "status": status,
            "inspection_notes": (
                "Quality acceptable" if status == "accepted"
                else "Minor defects on partial lot" if status == "partial_accept"
                else ""
            ),
        })
    return pd.DataFrame(rows)
