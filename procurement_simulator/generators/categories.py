from __future__ import annotations

import pandas as pd

from procurement_simulator.generators.base import category_id


def generate_categories(profile: dict) -> pd.DataFrame:
    rows = []
    for i, c in enumerate(profile["categories"]):
        rows.append({
            "category_id": category_id(i + 1),
            "name": c["name"],
            "spend_share": float(c["spend_share"]),
            "amount_mu": float(c["amount_mu"]),
            "amount_sigma": float(c["amount_sigma"]),
        })
    return pd.DataFrame(rows)
