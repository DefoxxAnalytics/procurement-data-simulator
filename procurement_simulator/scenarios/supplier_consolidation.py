from __future__ import annotations

import numpy as np
import pandas as pd


def apply(dfs: dict[str, pd.DataFrame], params: dict, rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    degree = float(params.get("degree", 0.5))
    if degree <= 0:
        return dfs
    degree = min(degree, 1.0)

    dfs = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in dfs.items()}
    transactions = dfs.get("transactions")
    suppliers = dfs.get("suppliers")
    if transactions is None or transactions.empty or suppliers is None or suppliers.empty:
        return dfs

    tier_map = dict(zip(suppliers["supplier_id"], suppliers["tier"]))

    def is_tail(sid):
        return tier_map.get(sid) == "tail"

    def is_tier1(sid):
        return tier_map.get(sid) == "tier_1"

    tail_mask = transactions["supplier_id"].map(is_tail).fillna(False)
    tail_idx = transactions.index[tail_mask]
    n_reassign = int(len(tail_idx) * degree)
    if n_reassign <= 0:
        return dfs
    reassign_idx = rng.choice(tail_idx, size=n_reassign, replace=False)

    tier1_ids = suppliers.loc[suppliers["tier"] == "tier_1", "supplier_id"].to_numpy()
    if len(tier1_ids) == 0:
        return dfs
    new_sup = rng.choice(tier1_ids, size=n_reassign)
    dfs["transactions"].loc[reassign_idx, "supplier_id"] = new_sup

    return dfs
