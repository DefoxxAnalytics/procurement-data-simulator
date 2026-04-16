from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


def _shift_date(value, days: int):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    if isinstance(value, pd.Timestamp):
        return (value + pd.Timedelta(days=days)).date()
    if isinstance(value, date):
        return value + timedelta(days=days)
    return value


def apply(dfs: dict[str, pd.DataFrame], params: dict, rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    rate = float(params.get("rate", 0.02))
    if rate <= 0:
        return dfs

    dfs = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in dfs.items()}
    invoices = dfs.get("invoices")
    pos = dfs.get("purchase_orders")
    transactions = dfs.get("transactions")

    if invoices is not None and not invoices.empty:
        n_dup = max(1, int(len(invoices) * rate * 0.4))
        dup_idx = rng.choice(invoices.index, size=min(n_dup, len(invoices)), replace=False)
        dups = invoices.loc[dup_idx].copy()
        dups["invoice_id"] = dups["invoice_id"].astype(str) + "-DUP"
        dups["invoice_number"] = dups["invoice_number"].astype(str) + "-DUP"
        shifts = rng.integers(1, 6, size=len(dups))
        dups["invoice_date"] = [_shift_date(v, int(d)) for v, d in zip(dups["invoice_date"].tolist(), shifts)]
        dups["has_exception"] = True
        dups["exception_type"] = "duplicate"
        dups["match_status"] = "exception"
        dups["status"] = "exception"
        dfs["invoices"] = pd.concat([invoices, dups], ignore_index=True)

        n_round = max(1, int(len(invoices) * rate * 0.3))
        round_idx = rng.choice(dfs["invoices"].index, size=min(n_round, len(dfs["invoices"])), replace=False)
        bumped = np.round(dfs["invoices"].loc[round_idx, "invoice_amount"] / 1000) * 1000
        bumped = bumped.where(bumped > 0, 1000.0)
        dfs["invoices"].loc[round_idx, "invoice_amount"] = bumped.values
        dfs["invoices"].loc[round_idx, "tax_amount"] = np.round(bumped.values * 0.08, 2)
        dfs["invoices"].loc[round_idx, "net_amount"] = np.round(bumped.values * 0.92, 2)

    if pos is not None and not pos.empty:
        n_split = max(1, int(len(pos) * rate * 0.3))
        split_idx = rng.choice(pos.index, size=min(n_split, len(pos)), replace=False)
        splits = pos.loc[split_idx].copy()
        splits["po_id"] = splits["po_id"].astype(str) + "-S2"
        splits["po_number"] = splits["po_number"].astype(str) + "-S2"
        splits["total_amount"] = np.round(splits["total_amount"].astype(float) * 0.55, 2)
        splits["tax_amount"] = np.round(splits["total_amount"].astype(float) * 0.08, 2)
        splits["is_contract_backed"] = False
        splits["contract_id"] = None
        pos.loc[split_idx, "total_amount"] = np.round(pos.loc[split_idx, "total_amount"].astype(float) * 0.45, 2)
        pos.loc[split_idx, "tax_amount"] = np.round(pos.loc[split_idx, "total_amount"].astype(float) * 0.08, 2)
        dfs["purchase_orders"] = pd.concat([pos, splits], ignore_index=True)

    if transactions is not None and not transactions.empty:
        n_round_tx = max(1, int(len(transactions) * rate * 0.2))
        idx = rng.choice(transactions.index, size=min(n_round_tx, len(transactions)), replace=False)
        bumped = np.round(transactions.loc[idx, "amount"] / 500) * 500
        bumped = bumped.where(bumped > 0, 500.0)
        dfs["transactions"].loc[idx, "amount"] = bumped.values

    return dfs
