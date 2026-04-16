from __future__ import annotations

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import supplier_id


def generate_suppliers(profile: dict, rng: np.random.Generator) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Returns (suppliers_df, suppliers_by_category).

    suppliers_by_category maps category name -> list of supplier_ids assigned
    to that category (named first, then a slice of tail vendors).
    """
    cats = profile["categories"]
    cities = profile["tail_cities"]
    regions = profile["tail_regions"]

    rows: list[dict] = []
    next_idx = 1
    seen_names: set[str] = set()
    suppliers_by_cat: dict[str, list[str]] = {c["name"]: [] for c in cats}
    name_to_id: dict[str, str] = {}

    for ci, cat in enumerate(cats):
        for name in cat["named_suppliers"]:
            if name in name_to_id:
                suppliers_by_cat[cat["name"]].append(name_to_id[name])
                continue
            sid = supplier_id(next_idx)
            next_idx += 1
            rows.append({
                "supplier_id": sid,
                "name": name,
                "tier": "tier_1" if cat["named_suppliers"].index(name) < max(3, len(cat["named_suppliers"]) // 3)
                        else "tier_2",
                "primary_category": cat["name"],
                "is_named": True,
            })
            name_to_id[name] = sid
            seen_names.add(name)
            suppliers_by_cat[cat["name"]].append(sid)

    tail_suppliers: list[str] = []
    for template, count in profile["tail_supplier_templates"]:
        for _ in range(int(count)):
            base = template.format(
                city=cities[int(rng.integers(0, len(cities)))],
                region=regions[int(rng.integers(0, len(regions)))],
            )
            name = base
            suffix = 1
            while name in seen_names:
                suffix += 1
                name = f"{base} #{suffix}"
            seen_names.add(name)
            sid = supplier_id(next_idx)
            next_idx += 1
            rows.append({
                "supplier_id": sid,
                "name": name,
                "tier": "tail",
                "primary_category": "",
                "is_named": False,
            })
            tail_suppliers.append(sid)

    if cats and tail_suppliers:
        per_cat = max(10, len(tail_suppliers) // len(cats))
        for cat in cats:
            sample_size = min(per_cat, len(tail_suppliers))
            picks = rng.choice(tail_suppliers, size=sample_size, replace=False)
            suppliers_by_cat[cat["name"]].extend(picks.tolist())

    df = pd.DataFrame(rows)
    return df, suppliers_by_cat
