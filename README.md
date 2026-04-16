# Procurement Data Simulator

Generate **reproducible, provenance-stamped synthetic procurement datasets** for Healthcare, Higher Ed, and Manufacturing — without touching a database.

Each run emits a single `.zip` bundle containing 11 relational tables (CSV + XLSX + SQLite with FKs intact), a `recipe.yaml` for byte-exact reproduction, a `manifest.json` with SHA256 per file, a data dictionary, sample SQL queries, and a README.

![Status](https://img.shields.io/badge/status-v0.1.0-blue) ![Python](https://img.shields.io/badge/python-3.10+-green) ![License](https://img.shields.io/badge/license-internal-lightgrey)

---

## Quickstart

```bash
pip install -r procurement_simulator/requirements.txt
streamlit run procurement_simulator/app.py
```

Pick an industry in the header → adjust profile or stack scenarios → open the **Settings** tab → click **Generate Bundle** → download from the **Last Bundle** tab.

## What's inside a bundle

```
{industry}-{scenarios|baseline}-{UTC}.zip
└── {bundle-name}/
    ├── data/
    │   ├── categories.csv / suppliers.csv / transactions.csv
    │   ├── contracts.csv / contract_categories.csv
    │   ├── policies.csv / policy_violations.csv
    │   ├── purchase_requisitions.csv / purchase_orders.csv
    │   ├── goods_receipts.csv / invoices.csv
    ├── dataset.xlsx            # multi-sheet workbook
    ├── dataset.sqlite          # FKs enforced, queryable immediately
    ├── recipe.yaml             # reproducibility manifest
    ├── manifest.json           # SHA256 per file
    ├── data_dictionary.md      # every column explained
    ├── sample_queries.sql      # 10 ready-to-run queries
    └── README.md               # loading into pandas / Postgres / Power BI
```

## Features

- **3 industry baselines** with realistic category mixes, supplier tiers, seasonality, and spending policies
- **5 composable scenarios** — `plant_fraud`, `supplier_consolidation`, `category_shortage`, `pandemic_shock`, `maverick_spend`
- **Live preview** — 4 charts (Pareto · monthly trend · Benford · category mix) + metrics strip that update as you edit
- **Profile Studio** — editable category shares / μ / σ / seasonality via `st.data_editor`
- **Reproducibility contract** — same recipe + same seed ⇒ byte-identical bundle
- **Shared profiles** — the Django management commands in `scripts/` read the same industry DSL, so changes flow to both generators
- **Vectorized generation** — ~30 ms preview on 2 000 rows (cache hit: <2 ms), sub-10 s full 25k-row bundles

## Scripted use

```python
from procurement_simulator import (
    generate, GenerationConfig, get_profile, apply_scenarios, write_bundle,
)
from procurement_simulator.bundle.recipe import build_recipe
from procurement_simulator.profiles import PROFILES

industry = "healthcare"
profile = get_profile(industry)
cfg = GenerationConfig(n_transactions=25_000, seed=42, org_slug="demo")
scenarios = [{"name": "plant_fraud", "params": {"rate": 0.02}}]

dfs = generate(profile, cfg)
dfs = apply_scenarios(dfs, scenarios, seed=cfg.seed)
recipe = build_recipe(industry, cfg.to_dict(), profile, PROFILES[industry], scenarios)
write_bundle(dfs, recipe, "healthcare-with-fraud.zip")
```

## Project layout

```
.
├── procurement_simulator/     # main package
│   ├── app.py                 # Streamlit UI
│   ├── profiles/              # thin wrapper → scripts/_industry_profiles.py
│   ├── generators/            # pure-Python, DataFrame outputs (numpy-vectorized)
│   ├── scenarios/             # composable post-generation transforms
│   ├── bundle/                # CSV + XLSX + SQLite + recipe + manifest writers
│   ├── preview/               # plotly: pareto, monthly_trend, benford, category_mix
│   └── studio/                # plotly: spend_mix_donut, seasonality_bars
├── scripts/                   # shared profile DSL + existing Django seed commands
├── docs/
│   ├── procurement-data-simulator-design.md   # engineering design draft
│   ├── procurement-data-simulator-prd.md      # full product requirements
│   └── user-guide.md                          # comprehensive user guide
├── recipes/                   # reserved for source-controlled recipe fixtures
└── .streamlit/config.toml     # theme
```

## Documentation

- **[User Guide](docs/user-guide.md)** — everything about using the app: interface tour, every control, scenario walkthroughs, cookbook recipes, FAQ.
- **[PRD](docs/procurement-data-simulator-prd.md)** — product requirements, goals, non-goals, personas, success metrics, roadmap.
- **[Design Doc](docs/procurement-data-simulator-design.md)** — original engineering design that framed the studio / scenarios / bundle architecture.
- **In-app Guide tab** — the user guide is surfaced live inside the Streamlit app.

## Reproducibility

Every bundle includes `recipe.yaml`. Given the recipe + the installed generator version, anyone can regenerate byte-identical CSVs / SQLite / XLSX. `manifest.json` records SHA256 for every artifact so a consumer can verify integrity.

See the [User Guide §10](docs/user-guide.md#10-reproducibility--the-recipe--manifest-contract) for the exact reproduction recipe.

## Requirements

- Python 3.10+
- `streamlit >= 1.39` (for `st.segmented_control`, `st.data_editor`)
- `pandas`, `numpy`, `pyyaml`, `openpyxl`, `plotly`

All pinned in [`procurement_simulator/requirements.txt`](procurement_simulator/requirements.txt).

## Status

- **Phase 1 — MVP**: shipped (generators, bundle output)
- **Phase 2 — Simulator**: shipped (scenarios, live preview)
- **Phase 3 — Studio**: shipped (data-editor profile editor, baseline summary, theme, caching)
- **Phase 4 — Advanced**: proposed (recipe import UI, bundle history, scenario warnings, brand mark, sticky Generate). See [PRD §13](docs/procurement-data-simulator-prd.md#13-release-plan).

## License

Internal use — see organization policy.
