from __future__ import annotations

import numpy as np
import pandas as pd

from procurement_simulator.scenarios.category_shortage import apply as _category_shortage
from procurement_simulator.scenarios.maverick_spend import apply as _maverick_spend
from procurement_simulator.scenarios.pandemic_shock import apply as _pandemic_shock
from procurement_simulator.scenarios.plant_fraud import apply as _plant_fraud
from procurement_simulator.scenarios.supplier_consolidation import apply as _supplier_consolidation


SCENARIOS: dict[str, dict] = {
    "plant_fraud": {
        "fn": _plant_fraud,
        "label": "Plant fraud",
        "description": "Duplicate invoices, round-amount bias, split-PO patterns, after-hours approvals.",
        "params": {
            "rate": {"type": "float", "default": 0.02, "min": 0.0, "max": 0.20,
                     "help": "Share of invoices/POs affected."},
        },
    },
    "supplier_consolidation": {
        "fn": _supplier_consolidation,
        "label": "Supplier consolidation",
        "description": "Tier-1 suppliers absorb share from tail vendors.",
        "params": {
            "degree": {"type": "float", "default": 0.5, "min": 0.0, "max": 1.0,
                       "help": "Fraction of tail spend reassigned to tier-1."},
        },
    },
    "category_shortage": {
        "fn": _category_shortage,
        "label": "Category shortage",
        "description": "One category's spend is multiplied over a target quarter.",
        "params": {
            "category": {"type": "str", "default": "", "help": "Category name to inflate."},
            "quarter": {"type": "int", "default": 3, "min": 1, "max": 4,
                        "help": "Quarter (1-4) to target."},
            "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 10.0,
                           "help": "Multiplier applied to amounts in the target quarter."},
        },
    },
    "pandemic_shock": {
        "fn": _pandemic_shock,
        "label": "Pandemic shock",
        "description": "A month-wide disruption across categories (amount deflation + volatility).",
        "params": {
            "month": {"type": "str", "default": "2022-03", "help": "YYYY-MM of the shock."},
            "severity": {"type": "float", "default": 0.5, "min": 0.1, "max": 0.9,
                         "help": "Severity (0=no effect, 1=full collapse)."},
        },
    },
    "maverick_spend": {
        "fn": _maverick_spend,
        "label": "Maverick spend",
        "description": "Off-contract buying: force a share of POs to bypass existing contracts.",
        "params": {
            "rate": {"type": "float", "default": 0.15, "min": 0.0, "max": 0.5,
                     "help": "Fraction of contract-backed POs flipped to off-contract."},
        },
    },
}


def apply_scenarios(
    dfs: dict[str, pd.DataFrame],
    scenario_specs: list[dict],
    seed: int,
) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed + 997)
    current = dfs
    for spec in scenario_specs:
        name = spec["name"]
        if name not in SCENARIOS:
            raise KeyError(f"Unknown scenario: {name}")
        fn = SCENARIOS[name]["fn"]
        params = spec.get("params", {}) or {}
        current = fn(current, params, rng)
    return current
