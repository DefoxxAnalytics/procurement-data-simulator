from __future__ import annotations

import numpy as np
import pandas as pd


def apply(dfs: dict[str, pd.DataFrame], params: dict, rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    rate = float(params.get("rate", 0.15))
    if rate <= 0:
        return dfs

    dfs = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in dfs.items()}
    pos = dfs.get("purchase_orders")
    if pos is None or pos.empty:
        return dfs

    backed_idx = pos.index[pos["is_contract_backed"]]
    n = int(len(backed_idx) * rate)
    if n <= 0:
        return dfs
    flip_idx = rng.choice(backed_idx, size=n, replace=False)
    dfs["purchase_orders"].loc[flip_idx, "is_contract_backed"] = False
    dfs["purchase_orders"].loc[flip_idx, "contract_id"] = None

    return dfs
