# User Guide

A complete reference for the **Procurement Data Simulator**. This guide walks through every control in the app, every artifact in the output bundle, and the common tasks you'll run it for.

---

## 1. What this tool is

The Procurement Data Simulator generates **realistic, relational, reproducible procurement datasets** for three industries (Healthcare, Higher Ed, Manufacturing) — without touching a database.

Each run emits a single `.zip` bundle containing:

- 11 relational tables as CSV, multi-sheet XLSX, and a fully-joined SQLite database
- A `recipe.yaml` that lets anyone regenerate the same dataset byte-for-byte
- A `manifest.json` with SHA256 hashes for every file (integrity check)
- A data dictionary, sample SQL queries, and a README

Typical uses: demo data for pitches, training sets for fraud-detection models, stress inputs for ETL pipelines, teaching material for procurement analytics.

---

## 2. Quick start

### Install

```bash
pip install -r procurement_simulator/requirements.txt
```

### Run

From the **repository root** (so the `.streamlit/config.toml` theme is picked up):

```bash
streamlit run procurement_simulator/app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`). Open it in your browser.

### Generate your first bundle

1. Pick an industry in the header (Healthcare is selected by default).
2. Click the **Settings** tab at the bottom.
3. Accept the defaults (25 000 transactions, seed 42, past 3 years).
4. Click **Generate Bundle**.
5. Click the **Last Bundle** tab → **Download .zip**.

That's it. You have a complete, reproducible procurement dataset.

---

## 3. Interface tour

The app is laid out top-to-bottom:

```
┌─ Header ─────────────────────────────────────────────────────┐
│ Title · Industry picker · Status pills (seed/rows/preview ms)│
├─ Baseline summary card ──────────────────────────────────────┤
│ Baseline name · category count · top-3 · seasonal peaks      │
├─ Main area (3 columns) ──────────────────────────────────────┤
│ Profile Studio │ Scenario Stack │ Live Preview               │
├─ Tabs ───────────────────────────────────────────────────────┤
│ Settings │ Last Bundle │ Guide                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 Header bar

- **Industry segmented control** — switch between Healthcare, Higher Ed, Manufacturing. Switching resets profile edits; your scenario stack is preserved.
- **Status pills** on the right:
  - `seed` — current RNG seed
  - `rows` — target transaction count
  - `scenarios` — number of scenarios on the stack
  - `preview` — wall-clock time of the last preview generation (cache hits will be <2 ms)
  - `custom N edit(s)` — yellow pill appears when you've edited the profile away from baseline

### 3.2 Baseline summary card

Always shows the **raw** industry baseline — category count, top-3 categories by spend share, seasonal peaks. Stays anchored even when you edit, so you always know what you diverged from.

### 3.3 Main area

Three columns, side-by-side:

- **Profile Studio** — edit category shares and seasonality (see §4)
- **Scenario Stack** — add and order what-if scenarios (see §5)
- **Live Preview** — 4-metric strip + 4 charts that update as you edit (see §6)

### 3.4 Tabs

- **Settings** — identity, seed, dates, row counts, Generate Bundle button (see §7)
- **Last Bundle** — download, recipe, manifest of the most recent generate (see §8)
- **Guide** — this document

---

## 4. Profile Studio — shape the data-generating process

Your edits here change the *baseline* of the dataset: what categories dominate, how big transactions are, when spend peaks during the year.

### 4.1 Spend-mix donut + category editor

The donut shows the current category shares. Below it (in an expander) is an editable table with four columns:

| Column | What it controls |
|---|---|
| **Category** | Read-only. The category name. |
| **Share** | Relative share of total spend. Does **not** need to sum to 1.0 — it's normalized at generation. |
| **μ** (mu) | Log-normal mean for transaction amounts. Higher = bigger transactions on average. A μ of 8 means typical amounts around `e^8 ≈ $3 000`. |
| **σ** (sigma) | Log-normal variability. Higher = fatter tail (more extreme amounts). |

**Quick rules:**

- Raise a category's **share** to make it dominate the Pareto; lower it to suppress.
- Raise **μ** to model a category with bigger line items (e.g., capital equipment: μ ≈ 10–11).
- Raise **σ** to model a category with high volatility (e.g., research lab equipment mixes small reagents and expensive instruments: σ ≈ 1.8+).

The sum of all shares is shown live. It's rescaled to 1.0 when the bundle generates — you can leave it at anything non-zero.

**Reset** button clears your category edits back to baseline.

### 4.2 Seasonality bars + editor

The seasonality multipliers scale the *rate* of transactions per month. Mean is rescaled to 1.0 at generation, so a multiplier of **1.2** in December means "20% above the baseline rate." A multiplier of **0.75** in July means "25% below baseline."

The editor is a 12-row table — one row per month. Live mean is shown below.

**Typical industry patterns** (visible in the baselines):

- **Healthcare** — winter peak (cold/flu, end-of-year procedures), summer dip
- **Higher Ed** — tied to the academic calendar: big spikes in June/August (fiscal year, fall semester preparation), dip in May (post finals)
- **Manufacturing** — late-year push (Dec), summer plant shutdowns (July)

---

## 5. Scenario stack — composable what-ifs

Scenarios are **post-generation transforms**: each one takes the current dataset and mutates it. They stack in order — the first runs first.

### How to use the stack

1. Pick a scenario from the dropdown → click **Add**.
2. Adjust parameters in the expander.
3. Reorder with ↑ / ↓. Remove with **Remove**.
4. The preview re-renders instantly.

### 5.1 `plant_fraud`

**What it does:** injects three classic fraud patterns:

- **Duplicate invoices** (same amount, nearly-same date, `-DUP` suffix on the invoice number)
- **Round-amount bias** on a subset of invoices (amounts pulled toward the nearest $1 000)
- **Split POs** — one PO appears as two smaller ones (`-S2` suffix), often pushed off-contract

**Parameter:** `rate` (0.0–0.20). Roughly the fraction of invoices/POs affected. Start at `0.02` — realistic — and push to `0.10+` for obvious training data.

**Use it for:** training fraud-detection models, stress-testing 3-way match processes.

**Visual cue:** the **Benford** chart will tilt visibly — leading-digit distribution diverges from the natural curve.

### 5.2 `supplier_consolidation`

**What it does:** reassigns a fraction of tail-supplier transactions to tier-1 suppliers. Models what happens when a procurement team does a rationalization project.

**Parameter:** `degree` (0.0–1.0). `0.5` = 50% of tail transactions move to tier-1.

**Use it for:** modeling post-consolidation spend, seeing how Pareto concentration shifts.

**Visual cue:** the **Supplier Pareto** chart becomes steeper — tier-1 suppliers grow fatter, the tail shrinks.

### 5.3 `category_shortage`

**What it does:** amplifies transaction amounts in one category during a target quarter. Models a supply shortage that drove prices up.

**Parameters:**

- `category` — which category to affect (dropdown populated from your current profile)
- `quarter` — 1, 2, 3, or 4
- `multiplier` — 1.0 to 10.0 (3× is a typical shortage; 5–10× is severe)

**Use it for:** stress-testing forecasting models, modeling imaging-contrast shortage Q3 2022, raw-materials spike Q2.

**Visual cue:** the **Monthly trend** chart shows a bump; **Category mix** shows the category ballooning above its target share.

### 5.4 `pandemic_shock`

**What it does:** in the target month, drops a fraction of transactions entirely and deflates the remaining amounts with noise. Models a real disruption.

**Parameters:**

- `month` — `YYYY-MM` (e.g. `2022-03`)
- `severity` — 0.1 to 0.9. `0.5` = 50% drop with noise.

**Use it for:** modeling supply-chain collapse, COVID-like disruption, region-specific crisis.

**Visual cue:** a crater in the **Monthly trend**.

### 5.5 `maverick_spend`

**What it does:** flips a share of contract-backed POs to off-contract. Models buyers going around preferred suppliers and contracts.

**Parameter:** `rate` (0.0–0.5). `0.15` is a realistic "leaky contract compliance" rate.

**Use it for:** building dashboards that highlight off-contract spend, training models that flag maverick buyers.

**Visual cue:** mostly invisible in the standard 4 charts — check the SQL `is_contract_backed` distribution in the bundle.

### 5.6 Order matters

Scenarios compose, and order affects the result:

- `supplier_consolidation` **then** `plant_fraud` → fraud is injected into the already-consolidated supplier base (fewer, bigger duplicates)
- `plant_fraud` **then** `supplier_consolidation` → some of the duplicate invoices get their supplier reassigned by the consolidation pass (rare)

For most analyses, put **shape-changing** scenarios first (consolidation, shortage, shock) and **noise-injecting** scenarios last (fraud, maverick).

---

## 6. Live Preview — reading the charts

The preview runs on a **2 000-transaction sample** (not your full target count) for speed. It updates on every edit.

### 6.1 The 4-metric strip

- **Total spend** — sum of the sample's transaction amounts (not the full target)
- **Avg txn** — mean transaction amount
- **Top-10 share** — what % of total spend the top 10 suppliers account for. Higher = more concentrated Pareto.
- **Invoice exceptions** — % of invoices with match-status `exception`. Normal is ~20%; `plant_fraud` drives this up.

### 6.2 Supplier Pareto

Top 20 suppliers by spend (bars) + cumulative % line. Classic "80/20" check — a healthy procurement environment typically has the top 20 suppliers at 60–80% cumulative.

### 6.3 Monthly spend trend

Line chart of monthly spend. Should match your seasonality settings: peaks where you expect, troughs where you expect. Shocks and shortages appear as bumps/craters.

### 6.4 Benford first-digit distribution

Natural numeric data follows Benford's Law — leading digit `1` appears ~30% of the time, `9` only ~5%. Observed bars should hug the orange expected line.

**When it diverges:** `plant_fraud` injects round-amount bias, which inflates digits 1/2/5 and compresses others. If the distribution shifts visibly, that's a fraud signal.

### 6.5 Category mix (target vs. actual)

Gray bars = target share (from your profile). Blue bars = actual share in the sample. They should be close — any big gap indicates your edits or scenarios significantly changed the relative weights.

---

## 7. Settings tab

### 7.1 Identity

- **Org slug** — short code used inside generated IDs (e.g. `PO-UCH-2024-00123`). Defaults to the industry prefix; override if you're generating multiple datasets and want distinguishable IDs.
- **Org name** (optional) — display name. Blank = use the baseline's name (e.g., "Mercy Regional Medical Center").

### 7.2 Reproducibility

- **Seed** — any integer. Same seed + same recipe = identical bundle. Change the seed to get a different "parallel universe" with the same profile and scenarios.

### 7.3 Date range

- **Start date** — earliest transaction date. Default is 3 years before today.
- **End date** — latest transaction date. Default is today.
- Transaction dates are distributed across this range, weighted by seasonality.

### 7.4 Row counts

- **Auto-scale** (default, recommended) — set the transaction count and everything else follows realistic ratios:
  - Contracts: ~0.3% of transactions (minimum 20)
  - PRs: ~2%
  - POs: ~1.6%
  - GRs: ~1.4%
  - Invoices: ~1.2%
  - Violations: ~0.6%
- **Manual** — disable auto-scale and set each entity count independently via a table. Use this when you want a specific ratio (e.g., many violations against few transactions for a fraud-heavy training set).

### 7.5 Generate Bundle

The button is disabled if the date range is invalid. On click, the generator runs, scenarios apply, and the bundle is written to memory. Success flashes a message pointing you at the **Last Bundle** tab.

---

## 8. The bundle — what you get

The zip name encodes what's inside:

```
{industry}-{scenarios|baseline}-{UTC-timestamp}.zip

Examples:
  healthcare-baseline-20260416T123045Z.zip
  higher-ed-with-plant_fraud-maverick_spend-20260416T123101Z.zip
```

Unzipped:

```
{bundle-name}/
├── data/
│   ├── categories.csv
│   ├── suppliers.csv
│   ├── transactions.csv
│   ├── contracts.csv
│   ├── contract_categories.csv     ← M2M link table
│   ├── policies.csv
│   ├── policy_violations.csv
│   ├── purchase_requisitions.csv
│   ├── purchase_orders.csv
│   ├── goods_receipts.csv
│   └── invoices.csv
├── dataset.xlsx          ← same 11 tables as worksheets
├── dataset.sqlite        ← same data, FKs enforced, queryable immediately
├── recipe.yaml           ← everything needed to regenerate this bundle
├── manifest.json         ← SHA256 + size + row count per file
├── data_dictionary.md    ← every column explained
├── sample_queries.sql    ← 10 ready-to-run queries
└── README.md             ← loading into pandas / Postgres / Power BI
```

All IDs are stable strings (`SUP-00042`, `PO-UCH-2024-00123`, etc.) that join cleanly across tables.

---

## 9. Loading the data

### 9.1 pandas

```python
import pandas as pd

suppliers = pd.read_csv("data/suppliers.csv")
transactions = pd.read_csv("data/transactions.csv", parse_dates=["date"])

# Join supplier name onto transactions
joined = transactions.merge(suppliers[["supplier_id", "name"]], on="supplier_id")
joined.groupby("name")["amount"].sum().nlargest(10)
```

### 9.2 SQLite (recommended for exploration)

```bash
sqlite3 dataset.sqlite < sample_queries.sql
```

Or interactively:

```bash
sqlite3 dataset.sqlite
sqlite> .tables
sqlite> SELECT COUNT(*) FROM transactions;
sqlite> PRAGMA foreign_key_check;    -- should return empty
```

### 9.3 Excel

Open `dataset.xlsx` — each of the 11 tables is a sheet. Pivot tables work immediately.

### 9.4 Postgres

```bash
sqlite3 dataset.sqlite .dump | psql your_database
```

The dump is standard SQL (`CREATE TABLE` + `INSERT`) with FK constraints included.

### 9.5 Power BI

Point Power BI at `dataset.sqlite` via an ODBC SQLite driver, or load the CSVs directly from the `data/` folder and define relationships using the column names (`supplier_id`, `category_id`, `po_id`, etc.).

### 9.6 DuckDB

```python
import duckdb
con = duckdb.connect()
con.execute("CREATE VIEW transactions AS SELECT * FROM read_csv_auto('data/transactions.csv')")
# ...
```

---

## 10. Reproducibility — the recipe + manifest contract

### 10.1 `recipe.yaml` — how to regenerate

Every bundle includes its recipe. It contains only what's needed to reproduce the data:

```yaml
generator_version: "0.1.0"
industry: healthcare
config:
  seed: 42
  n_transactions: 25000
  # ...
profile_overrides:                # only diffs vs. baseline
  categories:
    - name: Pharmaceuticals
      spend_share: 0.45
scenarios:
  - name: plant_fraud
    params: { rate: 0.05 }
```

To reproduce:

```python
import yaml, pathlib
from procurement_simulator import generate, GenerationConfig, apply_scenarios, write_bundle
from procurement_simulator.bundle.recipe import apply_overrides
from procurement_simulator.profiles import PROFILES

recipe = yaml.safe_load(pathlib.Path("recipe.yaml").read_text())
baseline = PROFILES[recipe["industry"]]
profile = apply_overrides(baseline, recipe.get("profile_overrides") or {})
cfg = GenerationConfig.from_dict(recipe["config"])
dfs = generate(profile, cfg)
dfs = apply_scenarios(dfs, recipe["scenarios"], seed=cfg.seed)
write_bundle(dfs, recipe, "reproduced.zip")
```

Content-stable files (CSVs, SQLite, recipe, dictionary, README, queries) will be byte-identical. Only timestamps (`manifest.json`, bundle name) will differ.

### 10.2 `manifest.json` — integrity check

```json
{
  "bundle_name": "...",
  "generator_version": "0.1.0",
  "generated_at_utc": "2026-04-16T12:30:45+00:00",
  "seed": 42,
  "scenarios": ["plant_fraud"],
  "row_counts": { "transactions": 25000, ... },
  "files": {
    "data/transactions.csv": {
      "size_bytes": 1547832,
      "sha256": "a3f2..."
    },
    ...
  }
}
```

To verify a bundle hasn't been tampered with:

```python
import hashlib, json
from pathlib import Path

manifest = json.loads(Path("manifest.json").read_text())
for rel_path, info in manifest["files"].items():
    actual = hashlib.sha256(Path(rel_path).read_bytes()).hexdigest()
    assert actual == info["sha256"], f"Tampered: {rel_path}"
```

---

## 11. Cookbook — common tasks

### 11.1 Generate a fraud training set

1. Healthcare industry.
2. Add `plant_fraud` with `rate = 0.08` (aggressive, clearly labeled).
3. In Settings, turn off auto-scale and bump **Policy Violations** to 1 000.
4. Generate.

Train your model on `policy_violations.csv` joined to `invoices.csv`, using the `-DUP` suffix as positive labels.

### 11.2 Stress-test a Pareto dashboard

1. Any industry.
2. Add `supplier_consolidation` with `degree = 0.7`.
3. Settings: `n_transactions = 100 000`.
4. Generate.

The top 20 suppliers should end up at >85% cumulative share.

### 11.3 Model a Q3 imaging shortage

1. Healthcare.
2. Add `category_shortage` with `category = Imaging & Radiology`, `quarter = 3`, `multiplier = 4`.
3. Generate.

Check `transactions.csv` filtered to `category_id` for imaging — Q3 amounts will be ~4× their neighbors.

### 11.4 Create a teaching dataset (clean, reproducible)

1. Any industry.
2. **No scenarios** on the stack.
3. Seed = student cohort ID (for identical outputs across the class).
4. Settings: `n_transactions = 10 000` (fast to load in Jupyter).
5. Generate. Distribute the zip.

Students use `sample_queries.sql` to get oriented.

### 11.5 Audit a bundle's integrity

Given a zip file that someone handed you:

```bash
unzip bundle.zip -d /tmp/check
cd /tmp/check/*/
python -c "
import hashlib, json, pathlib
m = json.loads(pathlib.Path('manifest.json').read_text())
for f, info in m['files'].items():
    h = hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
    ok = h == info['sha256']
    print(('OK ' if ok else 'BAD '), f)
"
```

### 11.6 Produce 3 "parallel universes" of the same scenario

Same profile, same scenarios, different seeds:

```python
from procurement_simulator import *
from procurement_simulator.bundle.recipe import build_recipe
from procurement_simulator.profiles import PROFILES

profile = get_profile("manufacturing")
scenarios = [{"name": "pandemic_shock", "params": {"month": "2022-03", "severity": 0.6}}]
for seed in (1, 2, 3):
    cfg = GenerationConfig(seed=seed, n_transactions=25_000)
    dfs = generate(profile, cfg)
    dfs = apply_scenarios(dfs, scenarios, seed=seed)
    recipe = build_recipe("manufacturing", cfg.to_dict(), profile, PROFILES["manufacturing"], scenarios)
    write_bundle(dfs, recipe, f"manufacturing-shock-seed{seed}.zip")
```

---

## 12. Troubleshooting & FAQ

**My preview looks empty / flat.**
Double-check that at least one category has `spend_share > 0`. The total doesn't need to be 1, but it can't be 0.

**The Generate button is disabled.**
Your date range is invalid — start date must be strictly before end date.

**Switching industries lost my scenario params.**
Scenarios persist across industry switches, but `category_shortage` references a category name — if you switch to an industry that doesn't have that category, the scenario still runs but targets nothing. Fix: update the category dropdown for that scenario after switching.

**"Preview ms" pill shows a high number every time.**
Likely cause: every edit produces a *different* cache key. If you're typing in a text field that's plumbed into the profile, each keystroke is a new key. Sliders and data-editor cells only commit on blur or slider release, so they cache well.

**I can't reproduce a recipe.**
Check the `generator_version` line in `recipe.yaml` matches the installed `procurement_simulator` version. Bumps in major/minor may introduce non-backward-compatible changes to the generator.

**SQLite says "no such column" when I query.**
You're likely joining on the wrong column name. All FK columns use the `_id` suffix (e.g., `supplier_id`, `po_id`). The CSV column headers match the SQLite column names exactly — check `data_dictionary.md`.

**The bundle is much smaller than I expected.**
The target row counts are upper bounds. If, say, only a small fraction of POs are receivable, the GR count is capped below the target. Look at `manifest.json` → `row_counts` for actuals.

**Memory pressure when generating 200 000 transactions.**
200k is the hard cap. Typical peak is <600 MB. If you're running into trouble, lower `n_transactions` and trade volume for multiple bundles.

**I want to add a new industry.**
Add a dict in `scripts/_industry_profiles.py` matching the existing schema (categories, seasonality, suppliers, departments, cost_center_prefix, payment_terms, policies, tail_cities, tail_regions). Register it in the `PROFILES` dict at the bottom. The UI will pick it up after adding an entry to `INDUSTRIES` in `procurement_simulator/app.py`.

---

## 13. Glossary

- **Baseline** — the unedited industry profile as defined in `scripts/_industry_profiles.py`.
- **Bundle** — the single `.zip` containing the full reproducible dataset and its provenance.
- **Live preview** — the 4-chart strip that updates on every edit, powered by a 2 000-transaction sample and Streamlit's cache.
- **Manifest** — `manifest.json`, the generation-metadata + SHA256-per-file artifact.
- **Profile** — the declarative dict for an industry (categories, seasonality, suppliers, departments, policies).
- **Recipe** — `recipe.yaml`, the reproducibility artifact capturing industry + overrides + scenarios + config.
- **Scenario** — a post-generation, pure-function transform that mutates DataFrames to model a real-world phenomenon (fraud, consolidation, shock, …).
- **Scenario stack** — ordered list of scenarios applied sequentially.
- **Tier-1 / tier-2 / tail** — supplier tier classification. Tier-1 are large named vendors (e.g., Cardinal Health), tier-2 are smaller named, tail are synthesized city/region-specific vendors.

---

*Found a bug or have a request? See `docs/procurement-data-simulator-prd.md` for the product roadmap (Phase 4+ backlog).*
