from __future__ import annotations

import numpy as np
import pandas as pd


def apply(dfs: dict[str, pd.DataFrame], params: dict, rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    category = params.get("category") or ""
    quarter = int(params.get("quarter", 3))
    multiplier = float(params.get("multiplier", 3.0))
    if not category or multiplier == 1.0:
        return dfs
    q_months = {1: (1, 2, 3), 2: (4, 5, 6), 3: (7, 8, 9), 4: (10, 11, 12)}.get(quarter, (7, 8, 9))

    dfs = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in dfs.items()}
    categories = dfs.get("categories")
    transactions = dfs.get("transactions")
    if categories is None or transactions is None:
        return dfs

    cat_row = categories.loc[categories["name"] == category]
    if cat_row.empty:
        return dfs
    cid = cat_row.iloc[0]["category_id"]

    dates = pd.to_datetime(transactions["date"])
    mask = (transactions["category_id"] == cid) & (dates.dt.month.isin(q_months))
    if mask.any():
        dfs["transactions"].loc[mask, "amount"] = np.round(
            transactions.loc[mask, "amount"].astype(float) * multiplier, 2
        )

    return dfs
