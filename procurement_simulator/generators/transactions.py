from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import transaction_id

_AMOUNT_FLOOR = 1.00
_AMOUNT_CEILING = 5_000_000.00


def generate_transactions(
    profile: dict,
    suppliers_by_cat: dict[str, list[str]],
    n_transactions: int,
    start_date: date,
    end_date: date,
    rng: np.random.Generator,
) -> pd.DataFrame:
    cats = profile["categories"]
    seasonality = np.asarray(profile["seasonality"], dtype=float)
    if seasonality.shape != (12,):
        raise ValueError("seasonality must be length 12")

    total_days = (end_date - start_date).days
    if total_days <= 0:
        raise ValueError("end_date must be after start_date")

    shares = np.array([c["spend_share"] for c in cats], dtype=float)
    shares = shares / shares.sum()
    counts = np.floor(shares * n_transactions).astype(int)
    counts[-1] = int(n_transactions - counts[:-1].sum())

    chunks: list[pd.DataFrame] = []
    next_seq = 1

    day_index = np.arange(total_days + 1)
    days_array = np.array([start_date + timedelta(days=int(d)) for d in day_index])
    months_for_days = np.array([d.month for d in days_array], dtype=int)
    day_weights = seasonality[months_for_days - 1]
    day_weights = day_weights / day_weights.sum()

    for cat, n in zip(cats, counts):
        if n <= 0:
            continue
        sup_ids = suppliers_by_cat[cat["name"]]
        if not sup_ids:
            continue

        named_count = len(cat["named_suppliers"])
        named = sup_ids[:named_count]
        tail = sup_ids[named_count:]

        roll = rng.random(n)
        amounts = rng.lognormal(mean=cat["amount_mu"], sigma=cat["amount_sigma"], size=n)
        amounts = np.clip(amounts, _AMOUNT_FLOOR, _AMOUNT_CEILING)
        amounts = np.round(amounts, 2)

        chosen_days = rng.choice(day_index, size=n, p=day_weights)
        dates = days_array[chosen_days]

        sup_choices = np.empty(n, dtype=object)
        named_mask = roll < 0.75
        n_named = int(named_mask.sum())
        n_tail = n - n_named

        if named and n_named > 0:
            named_arr = np.array(named, dtype=object)
            ranks = np.arange(len(named), 0, -1, dtype=float)
            named_p = ranks / ranks.sum()
            sup_choices[named_mask] = rng.choice(named_arr, size=n_named, p=named_p)
        if tail and n_tail > 0:
            tail_arr = np.array(tail, dtype=object)
            sup_choices[~named_mask] = rng.choice(tail_arr, size=n_tail)
        elif n_tail > 0 and named:
            named_arr = np.array(named, dtype=object)
            sup_choices[~named_mask] = rng.choice(named_arr, size=n_tail)

        ids = [transaction_id(next_seq + i) for i in range(n)]
        next_seq += n

        chunks.append(pd.DataFrame({
            "transaction_id": ids,
            "date": dates,
            "category_id": cat.get("_id"),
            "category": cat["name"],
            "supplier_id": sup_choices,
            "amount": amounts,
        }))

    if not chunks:
        return pd.DataFrame(columns=["transaction_id", "date", "category_id", "category", "supplier_id", "amount"])

    df = pd.concat(chunks, ignore_index=True)
    df = df.sort_values("date").reset_index(drop=True)
    return df
