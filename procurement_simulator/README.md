# Procurement Data Simulator

Reproducible, provenance-stamped synthetic procurement datasets for Healthcare, Higher Ed, and Manufacturing.

## What it is

A standalone tool for generating procurement datasets that look real:

- 11 relational tables (suppliers, categories, transactions, contracts, PRs, POs, GRs, invoices, policies, policy violations, contract_categories)
- Industry-specific category mixes, seasonality, and supplier tiers
- Composable **scenario layers** (plant fraud, supplier consolidation, category shortages, pandemic shocks, maverick spend)
- Live preview of four charts that update as you edit
- Output as a single `.zip` **bundle**: CSVs, XLSX, SQLite (FKs intact), `recipe.yaml`, `manifest.json` (SHA256), data dictionary, sample SQL, README

## Quickstart

```bash
pip install -r procurement_simulator/requirements.txt
streamlit run procurement_simulator/app.py
```

Open the URL that Streamlit prints, pick an industry, tweak the sliders, optionally stack scenarios, and click **Generate Bundle**.

## Scripted use

```python
from procurement_simulator import generate, GenerationConfig, get_profile, apply_scenarios, write_bundle
from procurement_simulator.bundle.recipe import build_recipe
from procurement_simulator.profiles import PROFILES

industry = "healthcare"
profile = get_profile(industry)
cfg = GenerationConfig(n_transactions=25_000, seed=42, org_slug="demo")
dfs = generate(profile, cfg)
dfs = apply_scenarios(dfs, [{"name": "plant_fraud", "params": {"rate": 0.02}}], seed=cfg.seed)
recipe = build_recipe(industry, cfg.to_dict(), profile, PROFILES[industry],
                     [{"name": "plant_fraud", "params": {"rate": 0.02}}])
write_bundle(dfs, recipe, "healthcare-with-fraud.zip")
```

## Architecture

```
procurement_simulator/
├── profiles/       # thin wrapper around scripts/_industry_profiles.py (shared with Django)
├── generators/     # pure-Python generators (pd.DataFrame outputs)
│   ├── categories.py
│   ├── suppliers.py
│   ├── transactions.py     # numpy-vectorized
│   ├── contracts.py
│   ├── policies.py
│   ├── policy_violations.py
│   ├── purchase_requisitions.py
│   ├── purchase_orders.py
│   ├── goods_receipts.py
│   └── invoices.py
├── scenarios/      # pure functions (dfs, params, rng) -> dfs
│   ├── plant_fraud.py
│   ├── supplier_consolidation.py
│   ├── category_shortage.py
│   ├── pandemic_shock.py
│   └── maverick_spend.py
├── bundle/         # CSV + XLSX + SQLite + recipe + manifest + dictionary + README
├── preview/        # plotly charts for live preview
├── studio/         # plotly figures for profile editing
└── app.py          # Streamlit UI
```

One source of truth, two sinks: the Django management command `scripts/seed_industry_data.py`
reads the same profile data (`scripts/_industry_profiles.py`) that the simulator uses.

## Reproducibility

Every bundle includes a `recipe.yaml`. Two runs with the same recipe produce the same data
(modulo clock-dependent fields like `generated_at_utc`). `manifest.json` lists SHA256 hashes for each file.
