from __future__ import annotations

import numpy as np
import pandas as pd


def apply(dfs: dict[str, pd.DataFrame], params: dict, rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    month = str(params.get("month", "2022-03"))
    severity = float(params.get("severity", 0.5))
    if severity <= 0:
        return dfs
    severity = min(severity, 0.95)

    try:
        target_year, target_month = map(int, month.split("-")[:2])
    except Exception:
        return dfs

    dfs = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in dfs.items()}
    transactions = dfs.get("transactions")
    if transactions is None or transactions.empty:
        return dfs

    dates = pd.to_datetime(transactions["date"])
    mask = (dates.dt.year == target_year) & (dates.dt.month == target_month)
    n_affected = int(mask.sum())
    if n_affected == 0:
        return dfs

    drop_factor = 1.0 - severity
    noise = 1.0 + rng.normal(0, severity * 0.25, size=n_affected)
    new_amounts = transactions.loc[mask, "amount"].astype(float).values * drop_factor * noise
    new_amounts = np.clip(new_amounts, 1.0, None)
    dfs["transactions"].loc[mask, "amount"] = np.round(new_amounts, 2)

    drop_frac = severity * 0.6
    drop_idx = rng.choice(
        transactions.index[mask],
        size=int(n_affected * drop_frac),
        replace=False,
    )
    if len(drop_idx) > 0:
        dfs["transactions"] = dfs["transactions"].drop(index=drop_idx).reset_index(drop=True)

    return dfs
