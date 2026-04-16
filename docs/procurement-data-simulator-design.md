# Procurement Data Simulator — Design Proposal

> Status: design draft
> Scope: standalone app for generating synthetic procurement datasets across Healthcare, Higher Ed, and Manufacturing, independent of the Django project.

---

## 1. Context

The repo currently ships three industry profiles (`scripts/_industry_profiles.py`) and a Django management command (`scripts/seed_industry_data.py`) that writes directly to the procurement ORM models. The goal is a tool that lets us **independently generate synthetic datasets per industry and save them to CSV/Excel** — with a nice UI on top.

An initial sketch landed on "Streamlit with industry picker + download buttons." Re-reviewed with critical eyes, that design has real weaknesses:

- **Commodity shape.** Every synthetic-data tutorial looks identical. Nothing memorable.
- **Fixates on format (CSV vs xlsx), skips the interesting problems:** reproducibility, statistical realism, scenario injection, relational integrity, provenance.
- **Raw DataFrames are a thin deliverable.** A CSV with no seed, no config, no lineage, no data dictionary is a dataset no one can defend or re-create.
- **The UI was flat.** It didn't let users *see* how the three industries differ or *steer* the data toward scenarios they need (plant fraud, simulate shortage, etc.). The most interesting artifact in the repo — the `_industry_profiles.py` DSL — got reduced to a radio button.
- **Ignored the relational structure.** Procurement is graph-shaped (PR → PO → GR → Invoice; Supplier ↔ Category; Contract ↔ PO). Independent CSVs force consumers to re-stitch keys — that's a footgun.

## 2. Reframe

Don't build a "CSV generator." Build a **Procurement Data Simulator** that emits **reproducible, provenance-stamped dataset bundles**. The generator is table stakes; the differentiator is the *studio around it*.

## 3. The Design — Three Stacked Ideas

### 3.1 Profile Studio (direct manipulation, not forms)

The `_industry_profiles.py` dict is already a DSL for "what procurement looks like in industry X." Surface it as a visual editor rather than radio buttons:

- **Spend mix** rendered as an editable donut — drag slice edges to rebalance categories; total auto-normalizes to 100%.
- **Seasonality** as 12 draggable bars (mean stays ~1.0 via live rebalance).
- **Supplier tiers** as a tree: tier-1 named / tier-2 named / tail-synthesized, with counts you can nudge.
- **Amount distribution (μ/σ)**, **payment terms**, **policies** as tidy side panels.
- "Reset to Healthcare/Higher Ed/Manufacturing baseline" always one click away.

The user *sees* how the industries actually differ — pharmaceuticals dominance, academic-calendar seasonality, raw-materials ramp. It doubles as a teaching tool.

### 3.2 Scenario Stack (composable what-ifs)

On top of the base profile, let users add ordered scenario layers. Each scenario is a pure function that mutates the profile or post-processes transactions. Built-ins:

| Scenario | Effect |
|---|---|
| `plant_fraud(rate=0.02)` | duplicate invoices, round-amount bias, after-hours POs, split-PO patterns |
| `supplier_consolidation(degree=0.5)` | tier-1 absorbs tail share |
| `category_shortage(category, quarter, multiplier)` | e.g. imaging tripled in Q3 |
| `pandemic_shock(month, severity)` | category-wide disruption preset |
| `maverick_spend(rate=0.15)` | off-contract buying |

Order matters (chip list, drag-to-reorder). This turns the tool from "seed data utility" into "ground-truth generator for testing fraud detection, forecasting, and policy engines."

### 3.3 Live Preview (500-row sample, sub-second)

A strip of four small charts that update as the user edits:

- Supplier spend Pareto
- Monthly spend trend
- Benford first-digit distribution (shifts visibly when fraud scenario fires — instant feedback)
- Category mix vs. target

This is the "wow" — users *see* cause and effect. Scenarios become tangible rather than abstract.

## 4. Output — Dataset Bundle, Not Loose Files

Every "Generate" click produces a single `.zip`:

```
healthcare-with-fraud-v1/
├── data/
│   ├── suppliers.csv
│   ├── categories.csv
│   ├── purchase_requisitions.csv
│   ├── purchase_orders.csv
│   ├── goods_receipts.csv
│   ├── invoices.csv
│   ├── contracts.csv
│   └── policy_violations.csv
├── dataset.xlsx          # same tables, multi-sheet, for Excel users
├── dataset.sqlite        # same data, queryable, FKs intact
├── recipe.yaml           # profile + scenario stack + seed — reproducible
├── manifest.json         # generator version, timestamp, row counts, SHA256 per file
├── data_dictionary.md    # every column explained
├── sample_queries.sql    # "top 10 suppliers", "PO→invoice match rate", etc.
└── README.md             # loading into pandas / Postgres / Power BI
```

Three format tiers in one bundle:

- **CSVs** — pipelines and ETL
- **XLSX (multi-sheet)** — humans and Excel users
- **SQLite** — keys intact, queryable immediately

`recipe.yaml` + seed = anyone can reproduce the exact dataset forever. That provenance story is what makes the tool defensible for audit, research, and demo contexts.

## 5. UI Layout

```
┌─ Procurement Data Simulator ────────────────────────────────────┐
│ [ Healthcare ]  [ Higher Ed ]  [ Manufacturing ]   ← card strip │
├─────────────────────────────────────────────────────────────────┤
│ PROFILE STUDIO          │ SCENARIO STACK   │ LIVE PREVIEW       │
│  • Spend mix donut      │  + plant_fraud   │ [Pareto chart]     │
│  • Seasonality bars     │  + consolidation │ [Monthly trend]    │
│  • Supplier tiers       │  + shortage Q3   │ [Benford dist]     │
│  • Amount distribution  │  (drag to order) │ [Category mix]     │
│  • Payment terms        │                  │ [100-row sample]   │
├─────────────────────────────────────────────────────────────────┤
│ Rows: [slider 1k–200k]   Seed: [42]   [ Generate Bundle ]       │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Architecture

Two concerns to separate cleanly:

- **`generators/`** — pure Python, no Django. One module per industry (`healthcare.py`, `higher_ed.py`, `manufacturing.py`), sharing a common `base.py`. Each exposes `generate(config) -> dict[str, pd.DataFrame]`.
- **`app.py`** — Streamlit UI. Reads/writes profiles, applies scenarios, calls generators, emits the bundle.
- **`scenarios/`** — pure functions `(profile, dfs) -> (profile, dfs)`. Composable.
- **`bundle/`** — serialization: CSVs, XLSX writer, SQLite writer, manifest, recipe, data dictionary.

The existing Django management command becomes a thin wrapper that calls the same `generators.*` module and persists to ORM instead of CSVs. One source of truth, two sinks.

## 7. Trade-offs

- **Effort**: ~2–3 days to a polished MVP, ~1 week for the full studio + scenarios. A plain "industry picker + download" version is an afternoon. ~10× effort for ~100× differentiation.
- **Refactor cost**: live preview needs vectorized (numpy/pandas) generation, not the current row-by-row ORM-coupled loop. That refactor is the biggest chunk of the work but pays off in speed everywhere, including the existing Django command.
- **Profile Studio complexity**: editable donut slices need a minor custom component or a draggable bar-chart proxy. If too rich for MVP, ship sliders first and upgrade later.
- **Scenarios** tip the project from utility toward opinionated research tooling. Great if that's the ambition, overkill if just demo data is needed.

## 8. Phased Plan

| Phase | Scope | Est. effort |
|---|---|---|
| **Phase 1 — MVP** | Refactor generators to pure Python returning DataFrames. Streamlit with sliders (no studio). Full Dataset Bundle output (CSV + XLSX + SQLite + recipe + manifest + dictionary + README). | ~2 days |
| **Phase 2 — Simulator** | Live Preview charts. Scenario stack with 2–3 built-ins (fraud, consolidation, shortage). | ~2 days |
| **Phase 3 — Studio** | Visual direct-manipulation profile editor (donut, seasonality bars, supplier tier tree). | ~2–3 days |

The provenance story (bundle + recipe + manifest) alone — Phase 1 — already makes the tool distinctive. Phases 2 and 3 are where it becomes one-of-a-kind.

## 9. Open Questions

1. **Single-run vs. multi-run UX** — does the app generate one dataset per click, or accumulate a session of runs for side-by-side comparison?
2. **Recipe versioning** — store recipes in-repo under `recipes/` as source-controlled fixtures, or purely user-side?
3. **Django coupling** — keep the existing `seed_industry_data.py` wired to the new `generators/` package (shared source of truth), or let them diverge?
4. **Hosting** — local-only Streamlit, or eventually a shared internal deployment with run history?
