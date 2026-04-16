from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import streamlit as st

from procurement_simulator import (
    GenerationConfig,
    SCENARIOS,
    apply_scenarios,
    generate,
    get_profile,
)
from procurement_simulator.bundle.recipe import build_recipe, dump_recipe
from procurement_simulator.bundle.writer import write_bundle
from procurement_simulator.preview import benford, category_mix, monthly_trend, supplier_pareto
from procurement_simulator.profiles import PROFILES, normalize_seasonality, normalize_spend_share
from procurement_simulator.studio import seasonality_bars, spend_mix_donut

INDUSTRIES: list[tuple[str, str]] = [
    ("healthcare", "Healthcare"),
    ("higher-ed", "Higher Ed"),
    ("manufacturing", "Manufacturing"),
]
INDUSTRY_LABEL = dict(INDUSTRIES)
PREVIEW_ROWS = 2000
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_USER_GUIDE_PATH = _REPO_ROOT / "docs" / "user-guide.md"


def main() -> None:
    st.set_page_config(page_title="Procurement Data Simulator", layout="wide")
    _inject_styles()
    _init_state()

    header_slot = st.empty()
    industry = st.session_state["industry"]
    profile, industry = _resolve_profile()

    _render_baseline_summary(industry)

    studio_col, scenario_col, preview_col = st.columns([1.1, 0.9, 1.3])
    with studio_col:
        st.subheader("Profile Studio")
        _render_studio(profile, industry)
    with scenario_col:
        st.subheader("Scenario Stack")
        scenario_specs = _render_scenario_stack(profile)
    with preview_col:
        st.subheader("Live Preview")
        _render_preview(profile, scenario_specs)

    st.divider()
    settings_tab, bundle_tab, guide_tab = st.tabs(["Settings", "Last Bundle", "Guide"])
    with settings_tab:
        _render_settings_tab(industry, profile, scenario_specs)
    with bundle_tab:
        _render_bundle_tab()
    with guide_tab:
        _render_guide_tab()

    with header_slot.container():
        _render_header(industry, scenario_specs)


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
          .block-container { padding-top: 4.5rem; padding-bottom: 2rem; max-width: 1600px; }
          section[data-testid="stSidebar"] { display: none; }
          header[data-testid="stHeader"] { background: transparent; }
          .stPlotlyChart { padding: 0 !important; }
          h1, h2, h3 { letter-spacing: -0.01em; }

          .psim-header {
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 1rem;
              margin-bottom: 0.75rem;
              padding-bottom: 0.75rem;
              border-bottom: 1px solid #E5E7EB;
          }
          .psim-title {
              font-size: 1.3rem;
              font-weight: 600;
              color: #1F2937;
              letter-spacing: -0.02em;
          }
          .psim-title small {
              display: block;
              font-size: 0.75rem;
              color: #6B7280;
              font-weight: 400;
              letter-spacing: 0;
              margin-top: 0.1rem;
          }
          .psim-pills { display: flex; gap: 0.4rem; flex-wrap: wrap; justify-content: flex-end; }
          .psim-pill {
              display: inline-flex;
              align-items: center;
              gap: 0.35rem;
              padding: 0.2rem 0.6rem;
              border-radius: 999px;
              font-size: 0.78rem;
              font-variant-numeric: tabular-nums;
              background: #F3F4F6;
              color: #374151;
              border: 1px solid #E5E7EB;
          }
          .psim-pill .psim-pill-key {
              font-weight: 600;
              color: #4C78A8;
              text-transform: uppercase;
              font-size: 0.7rem;
              letter-spacing: 0.03em;
          }
          .psim-pill.psim-dirty { background: #FEF3C7; border-color: #FCD34D; color: #92400E; }
          .psim-pill.psim-dirty .psim-pill-key { color: #92400E; }

          .psim-summary {
              display: grid;
              grid-template-columns: 1.6fr 0.6fr 2.2fr 1.6fr;
              gap: 1.25rem;
              align-items: center;
              padding: 0.7rem 1rem;
              margin: 0.25rem 0 1rem 0;
              background: #F9FAFB;
              border: 1px solid #E5E7EB;
              border-radius: 10px;
              font-size: 0.84rem;
          }
          .psim-summary .psim-sum-label {
              display: block;
              font-size: 0.68rem;
              text-transform: uppercase;
              letter-spacing: 0.05em;
              color: #6B7280;
              font-weight: 600;
              margin-bottom: 0.15rem;
          }
          .psim-summary .psim-sum-value {
              color: #1F2937;
              font-variant-numeric: tabular-nums;
              line-height: 1.35;
          }
          .psim-summary .psim-sum-value strong { color: #4C78A8; font-weight: 600; }

          div[data-testid="stExpander"] details summary { font-weight: 500; }
          div[data-testid="stExpander"] { border-radius: 10px; }

          /* segmented_control polish */
          div[data-testid="stHorizontalBlock"] div[data-baseweb="tab-list"] { gap: 0.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    st.session_state.setdefault("industry", INDUSTRIES[0][0])
    st.session_state.setdefault("scenario_stack", [])
    st.session_state.setdefault("preview_ms", None)


def _render_header(industry: str, scenario_specs: list[dict]) -> None:
    settings = st.session_state.get("settings", {})
    seed = settings.get("seed", 42)
    n_tx = settings.get("n_transactions", 25_000)
    n_scen = len(scenario_specs)
    ms = st.session_state.get("preview_ms")
    ms_str = "—" if ms is None else f"{ms:.0f} ms"
    overrides = st.session_state.get("profile_overrides") or {}
    n_dirty = _override_count(overrides)

    pills = [
        ("seed", f"{seed}"),
        ("rows", f"{n_tx:,}"),
        ("scenarios", str(n_scen)),
        ("preview", ms_str),
    ]
    pill_html = "".join(
        f'<span class="psim-pill"><span class="psim-pill-key">{k}</span>{v}</span>'
        for k, v in pills
    )
    if n_dirty:
        pill_html += (
            f'<span class="psim-pill psim-dirty">'
            f'<span class="psim-pill-key">custom</span>{n_dirty} edit(s)</span>'
        )

    left, center, right = st.columns([2.4, 2.2, 3])
    with left:
        st.markdown(
            '<div class="psim-title">Procurement Data Simulator'
            '<small>Reproducible, provenance-stamped synthetic procurement data.</small>'
            '</div>',
            unsafe_allow_html=True,
        )
    with center:
        selected = st.segmented_control(
            "Industry",
            options=[s for s, _ in INDUSTRIES],
            format_func=lambda s: INDUSTRY_LABEL[s],
            default=industry,
            key="industry-segment",
            label_visibility="collapsed",
        )
        if selected and selected != industry:
            st.session_state["industry"] = selected
            st.session_state.pop("profile_overrides", None)
            st.rerun()
    with right:
        st.markdown(f'<div class="psim-pills">{pill_html}</div>', unsafe_allow_html=True)


def _render_baseline_summary(industry: str) -> None:
    baseline = PROFILES[industry]
    cats = baseline["categories"]
    n_cats = len(cats)
    top3 = sorted(cats, key=lambda c: c["spend_share"], reverse=True)[:3]
    top3_html = " · ".join(
        f"{_html_escape(c['name'])} <strong>{c['spend_share'] * 100:.0f}%</strong>"
        for c in top3
    )
    season = baseline["seasonality"]
    peak_idx = sorted(range(12), key=lambda i: -season[i])[:2]
    peaks_html = " · ".join(
        f"{_MONTHS[i]} <strong>×{season[i]:.2f}</strong>" for i in peak_idx
    )

    st.markdown(
        f"""
        <div class="psim-summary">
          <div>
            <span class="psim-sum-label">Baseline</span>
            <span class="psim-sum-value">{_html_escape(baseline['name'])}</span>
          </div>
          <div>
            <span class="psim-sum-label">Categories</span>
            <span class="psim-sum-value"><strong>{n_cats}</strong></span>
          </div>
          <div>
            <span class="psim-sum-label">Top 3 by spend share</span>
            <span class="psim-sum-value">{top3_html}</span>
          </div>
          <div>
            <span class="psim-sum-label">Seasonal peaks</span>
            <span class="psim-sum-value">{peaks_html}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _resolve_profile() -> tuple[dict, str]:
    industry = st.session_state["industry"]
    baseline = get_profile(industry)
    overrides = st.session_state.get("profile_overrides") or {}
    profile = _apply_overrides_session(baseline, overrides)
    return profile, industry


def _apply_overrides_session(baseline: dict, overrides: dict) -> dict:
    if not overrides:
        return baseline
    cat_overrides = overrides.get("categories") or {}
    for c in baseline["categories"]:
        delta = cat_overrides.get(c["name"])
        if delta:
            for k, v in delta.items():
                c[k] = v
    if "seasonality" in overrides:
        baseline["seasonality"] = list(overrides["seasonality"])
    return baseline


def _override_count(overrides: dict) -> int:
    n = 0
    cats = overrides.get("categories") or {}
    n += sum(len(v) for v in cats.values())
    if "seasonality" in overrides:
        n += 1
    return n


def _render_studio(profile: dict, industry: str) -> None:
    st.plotly_chart(spend_mix_donut(profile), use_container_width=True, key="donut")

    with st.expander("Category mix — edit share, μ, σ", expanded=False):
        cats_df = pd.DataFrame([
            {"name": c["name"], "spend_share": float(c["spend_share"]),
             "amount_mu": float(c["amount_mu"]), "amount_sigma": float(c["amount_sigma"])}
            for c in profile["categories"]
        ])
        edited = st.data_editor(
            cats_df,
            column_config={
                "name": st.column_config.TextColumn("Category", disabled=True, width="large"),
                "spend_share": st.column_config.NumberColumn(
                    "Share", min_value=0.0, max_value=1.0, step=0.005, format="%.3f",
                    help="Relative spend share. Normalized to sum to 1 at generation time.",
                ),
                "amount_mu": st.column_config.NumberColumn(
                    "μ", min_value=1.0, max_value=14.0, step=0.1, format="%.2f",
                    help="Log-normal mean for transaction amounts.",
                ),
                "amount_sigma": st.column_config.NumberColumn(
                    "σ", min_value=0.1, max_value=3.0, step=0.1, format="%.2f",
                    help="Log-normal sigma for transaction amounts.",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key=f"cat-editor-{industry}",
        )
        _sync_category_edits(edited, industry)
        total = edited["spend_share"].sum()
        msg_cols = st.columns([3, 1])
        with msg_cols[0]:
            st.caption(f"Shares sum to **{total:.3f}** (normalized to 1.0 at generation).")
        with msg_cols[1]:
            if st.button("Reset category edits", key="reset-cats", use_container_width=True):
                st.session_state.setdefault("profile_overrides", {}).pop("categories", None)
                st.rerun()

    st.plotly_chart(seasonality_bars(profile), use_container_width=True, key="seasonality")

    with st.expander("Seasonality — 12 monthly multipliers (mean ≈ 1.0)"):
        season_df = pd.DataFrame({
            "month": _MONTHS,
            "multiplier": [float(v) for v in profile["seasonality"]],
        })
        edited_season = st.data_editor(
            season_df,
            column_config={
                "month": st.column_config.TextColumn("Month", disabled=True, width="small"),
                "multiplier": st.column_config.NumberColumn(
                    "Multiplier", min_value=0.3, max_value=2.5, step=0.05, format="%.2f",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key=f"season-editor-{industry}",
            height=460,
        )
        _sync_seasonality_edits(edited_season, industry)
        mean = edited_season["multiplier"].mean()
        msg_cols = st.columns([3, 1])
        with msg_cols[0]:
            st.caption(f"Mean multiplier: **{mean:.3f}** (rescaled to 1.0 at generation).")
        with msg_cols[1]:
            if st.button("Reset seasonality", key="reset-season", use_container_width=True):
                st.session_state.setdefault("profile_overrides", {}).pop("seasonality", None)
                st.rerun()


def _sync_category_edits(edited: pd.DataFrame, industry: str) -> None:
    baseline = PROFILES[industry]
    base_by_name = {c["name"]: c for c in baseline["categories"]}
    diffs: dict[str, dict] = {}
    for _, row in edited.iterrows():
        name = row["name"]
        base = base_by_name.get(name)
        if not base:
            continue
        changes = {}
        for field in ("spend_share", "amount_mu", "amount_sigma"):
            if abs(float(row[field]) - float(base[field])) > 1e-9:
                changes[field] = float(row[field])
        if changes:
            diffs[name] = changes
    overrides = st.session_state.setdefault("profile_overrides", {})
    if diffs:
        overrides["categories"] = diffs
    else:
        overrides.pop("categories", None)


def _sync_seasonality_edits(edited: pd.DataFrame, industry: str) -> None:
    baseline = PROFILES[industry]
    edited_vals = [float(v) for v in edited["multiplier"].tolist()]
    if edited_vals == [float(v) for v in baseline["seasonality"]]:
        st.session_state.get("profile_overrides", {}).pop("seasonality", None)
    else:
        st.session_state.setdefault("profile_overrides", {})["seasonality"] = edited_vals


def _render_scenario_stack(profile: dict) -> list[dict]:
    scenarios_state = st.session_state.setdefault("scenario_stack", [])
    labels = {k: v["label"] for k, v in SCENARIOS.items()}
    existing = [s["name"] for s in scenarios_state]
    addable = [k for k in SCENARIOS if k not in existing]

    if addable:
        add_cols = st.columns([3, 1])
        with add_cols[0]:
            selection = st.selectbox(
                "Add scenario",
                options=[None] + addable,
                format_func=lambda k: "(select a scenario)" if k is None else labels[k],
                key="scenario-selector",
                label_visibility="collapsed",
            )
        with add_cols[1]:
            if st.button("Add", key="scenario-add-btn", disabled=selection is None, use_container_width=True):
                meta = SCENARIOS[selection]
                params = {k: p["default"] for k, p in meta["params"].items()}
                if selection == "category_shortage" and not params.get("category"):
                    params["category"] = profile["categories"][0]["name"]
                scenarios_state.append({"name": selection, "params": params})
                st.rerun()
    else:
        st.info("All scenarios already on stack.")

    if not scenarios_state:
        st.caption("No scenarios applied yet. Add one above to stack a composable what-if.")
        return scenarios_state

    st.caption(f"**Stack (executed in order):** {len(scenarios_state)}")
    for i, spec in enumerate(list(scenarios_state)):
        meta = SCENARIOS[spec["name"]]
        with st.expander(f"{i + 1}. {meta['label']}", expanded=True):
            st.caption(meta["description"])
            for pname, pdef in meta["params"].items():
                key = f"param-{i}-{pname}"
                current = spec["params"].get(pname, pdef["default"])
                if pdef["type"] == "float":
                    spec["params"][pname] = st.slider(
                        pname, min_value=float(pdef["min"]), max_value=float(pdef["max"]),
                        value=float(current), step=0.01, key=key,
                    )
                elif pdef["type"] == "int":
                    spec["params"][pname] = st.slider(
                        pname, min_value=int(pdef["min"]), max_value=int(pdef["max"]),
                        value=int(current), step=1, key=key,
                    )
                elif pdef["type"] == "str":
                    if pname == "category":
                        options = [c["name"] for c in profile["categories"]]
                        default_idx = options.index(current) if current in options else 0
                        spec["params"][pname] = st.selectbox(
                            pname, options=options, index=default_idx, key=key,
                        )
                    else:
                        spec["params"][pname] = st.text_input(
                            pname, value=str(current), key=key,
                            help=pdef.get("help"),
                        )

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("↑", key=f"up-{i}", disabled=(i == 0), use_container_width=True):
                    scenarios_state[i - 1], scenarios_state[i] = scenarios_state[i], scenarios_state[i - 1]
                    st.rerun()
            with c2:
                if st.button("↓", key=f"down-{i}", disabled=(i == len(scenarios_state) - 1), use_container_width=True):
                    scenarios_state[i + 1], scenarios_state[i] = scenarios_state[i], scenarios_state[i + 1]
                    st.rerun()
            with c3:
                if st.button("Remove", key=f"rm-{i}", use_container_width=True):
                    scenarios_state.pop(i)
                    st.rerun()

    return scenarios_state


@st.cache_data(show_spinner=False, max_entries=32)
def _cached_preview_dfs(profile_json: str, scenario_specs_json: str, seed: int, n_tx: int) -> dict:
    profile = json.loads(profile_json)
    scenario_specs = json.loads(scenario_specs_json)
    cfg = GenerationConfig(
        seed=seed,
        n_transactions=n_tx,
        n_prs=120, n_pos=80, n_grs=60, n_invoices=50, n_violations=30,
        org_slug="preview",
    )
    dfs = generate(_profile_for_gen(profile), cfg)
    if scenario_specs:
        dfs = apply_scenarios(dfs, scenario_specs, seed=seed)
    return dfs


def _render_preview(profile: dict, scenarios_state: list[dict]) -> None:
    seed = int(st.session_state.get("seed", 42))
    start = time.perf_counter()
    profile_json = json.dumps(profile, sort_keys=True, default=str)
    scenarios_json = json.dumps(scenarios_state, sort_keys=True, default=str)
    dfs = _cached_preview_dfs(profile_json, scenarios_json, seed, PREVIEW_ROWS)
    elapsed = (time.perf_counter() - start) * 1000
    st.session_state["preview_ms"] = elapsed

    _render_preview_summary(dfs)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.plotly_chart(supplier_pareto(dfs["transactions"], dfs["suppliers"]),
                        use_container_width=True, key="pareto")
        st.plotly_chart(benford(dfs["transactions"]), use_container_width=True, key="benford")
    with chart_cols[1]:
        st.plotly_chart(monthly_trend(dfs["transactions"]), use_container_width=True, key="trend")
        st.plotly_chart(category_mix(dfs["transactions"], dfs["categories"]),
                        use_container_width=True, key="mix")


def _render_preview_summary(dfs: dict) -> None:
    tx = dfs["transactions"]
    invoices = dfs.get("invoices")
    if tx.empty:
        return
    total = float(tx["amount"].sum())
    avg = float(tx["amount"].mean())
    top_share = 0.0
    if not dfs["suppliers"].empty:
        spend_by_sup = tx.groupby("supplier_id")["amount"].sum()
        top_share = float(spend_by_sup.nlargest(10).sum() / total) if total > 0 else 0.0
    exc_rate = 0.0
    if invoices is not None and not invoices.empty and "match_status" in invoices.columns:
        exc_rate = float((invoices["match_status"] == "exception").mean())

    cols = st.columns(4)
    cols[0].metric("Total spend", _fmt_money(total))
    cols[1].metric("Avg txn", _fmt_money(avg))
    cols[2].metric("Top-10 share", f"{top_share * 100:.0f}%")
    cols[3].metric("Invoice exceptions", f"{exc_rate * 100:.1f}%")


def _fmt_money(v: float) -> str:
    if v >= 1e9: return f"${v / 1e9:.2f}B"
    if v >= 1e6: return f"${v / 1e6:.2f}M"
    if v >= 1e3: return f"${v / 1e3:.1f}K"
    return f"${v:,.0f}"


_DEFAULT_RATIOS: dict[str, float] = {
    "n_prs": 0.020, "n_pos": 0.016, "n_grs": 0.014,
    "n_invoices": 0.012, "n_violations": 0.006, "n_contracts": 0.0032,
}
_RATIO_FLOORS: dict[str, int] = {
    "n_prs": 100, "n_pos": 80, "n_grs": 70, "n_invoices": 60,
    "n_violations": 20, "n_contracts": 20,
}
_ROW_COUNT_LABELS: dict[str, str] = {
    "n_transactions": "Transactions",
    "n_contracts": "Contracts",
    "n_prs": "Purchase Requisitions",
    "n_pos": "Purchase Orders",
    "n_grs": "Goods Receipts",
    "n_invoices": "Invoices",
    "n_violations": "Policy Violations",
}


def _render_settings_tab(industry: str, profile: dict, scenario_specs: list[dict]) -> None:
    settings = st.session_state.setdefault("settings", _default_settings(industry))
    _sync_settings_to_industry(settings, industry)

    ident_col, repro_col, date_col = st.columns(3)
    with ident_col:
        st.markdown("**Identity**")
        settings["org_slug"] = st.text_input(
            "Org slug", value=settings["org_slug"], key="settings-org-slug",
            help="Used in PR/PO/GR/Invoice/Contract numbers.",
        ).strip() or "demo"
        settings["org_name"] = st.text_input(
            "Org name (optional)", value=settings.get("org_name") or "", key="settings-org-name",
            help="Display name. Defaults to the industry profile name if blank.",
        ).strip() or None
    with repro_col:
        st.markdown("**Reproducibility**")
        seed_val = st.number_input(
            "Seed", min_value=0, max_value=2**31 - 1,
            value=int(settings["seed"]), step=1, key="settings-seed",
        )
        settings["seed"] = int(seed_val)
        st.session_state["seed"] = int(seed_val)
        st.caption("Same seed + same recipe ⇒ same bundle.")
    with date_col:
        st.markdown("**Date range**")
        settings["start_date"] = st.date_input(
            "Start date", value=settings["start_date"], key="settings-start-date",
            min_value=date(2010, 1, 1), max_value=date.today(),
        )
        settings["end_date"] = st.date_input(
            "End date", value=settings["end_date"], key="settings-end-date",
            min_value=settings["start_date"], max_value=date.today(),
        )
        if settings["end_date"] <= settings["start_date"]:
            st.warning("End date must be after start date.")

    st.markdown("**Row counts**")
    auto_scale = st.checkbox(
        "Auto-scale P2P entities from transaction count",
        value=settings.get("auto_scale", True),
        key="settings-auto-scale",
        help="Keeps PRs / POs / GRs / invoices / violations / contracts in realistic ratio.",
    )
    settings["auto_scale"] = auto_scale

    settings["n_transactions"] = st.slider(
        _ROW_COUNT_LABELS["n_transactions"],
        min_value=1_000, max_value=200_000,
        value=int(settings["n_transactions"]), step=1_000,
        key="settings-n-tx",
    )

    if auto_scale:
        derived = _derive_row_counts(settings["n_transactions"])
        for key in _ROW_COUNT_LABELS:
            if key == "n_transactions":
                continue
            settings[key] = derived[key]
        cols = st.columns(3)
        non_tx = [(k, v) for k, v in _ROW_COUNT_LABELS.items() if k != "n_transactions"]
        for i, (key, label) in enumerate(non_tx):
            with cols[i % 3]:
                st.metric(label, f"{settings[key]:,}")
    else:
        count_df = pd.DataFrame([
            {"Entity": _ROW_COUNT_LABELS[k], "key": k, "Count": int(settings[k])}
            for k in _ROW_COUNT_LABELS if k != "n_transactions"
        ])
        edited_counts = st.data_editor(
            count_df,
            column_config={
                "Entity": st.column_config.TextColumn("Entity", disabled=True, width="medium"),
                "key": None,
                "Count": st.column_config.NumberColumn(
                    "Count", min_value=0, max_value=10_000, step=10, format="%d",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="p2p-count-editor",
        )
        for _, row in edited_counts.iterrows():
            settings[row["key"]] = int(row["Count"])

    st.divider()
    action_col, info_col = st.columns([1, 3])
    with action_col:
        generate_clicked = st.button(
            "Generate Bundle", type="primary", use_container_width=True,
            disabled=settings["end_date"] <= settings["start_date"],
        )
    with info_col:
        total = settings["n_transactions"] + sum(
            settings[k] for k in _ROW_COUNT_LABELS if k != "n_transactions"
        )
        st.caption(
            f"Emits a .zip with CSVs, XLSX, SQLite (FKs intact), recipe.yaml, manifest.json (SHA256 per file), "
            f"data dictionary, sample queries, and README.  **~{total:,} total rows** across 11 tables."
        )

    if generate_clicked:
        _run_generation(industry, profile, scenario_specs, settings)


@st.cache_data(show_spinner=False)
def _load_user_guide(path_str: str, mtime_ns: int) -> str | None:
    """Read the user guide from disk. mtime_ns invalidates the cache on edit."""
    try:
        return Path(path_str).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def _render_guide_tab() -> None:
    try:
        mtime_ns = _USER_GUIDE_PATH.stat().st_mtime_ns
    except FileNotFoundError:
        mtime_ns = 0
    content = _load_user_guide(str(_USER_GUIDE_PATH), mtime_ns)
    if content is None:
        st.warning(
            f"User guide not found at `{_USER_GUIDE_PATH}`. "
            "See `docs/user-guide.md` in the repository, or restore the file."
        )
        return

    with st.container(height=720, border=False):
        st.markdown(content, unsafe_allow_html=False)


def _render_bundle_tab() -> None:
    bundle = st.session_state.get("last_bundle")
    if not bundle:
        st.info("No bundle generated yet. Configure **Settings**, then click **Generate Bundle**.")
        return

    st.success(f"Bundle ready: `{bundle['name']}`")
    dl_col, meta_col = st.columns([1, 2])
    with dl_col:
        st.download_button(
            "Download .zip",
            data=bundle["zip_bytes"],
            file_name=f"{bundle['name']}.zip",
            mime="application/zip",
            use_container_width=True,
        )
    with meta_col:
        st.caption(
            f"Total rows: {sum(bundle['row_counts'].values()):,}  ·  "
            f"size: {len(bundle['zip_bytes']):,} bytes  ·  "
            f"industry: {bundle['recipe'].get('industry', '?')}  ·  "
            f"seed: {bundle['recipe'].get('config', {}).get('seed', '?')}"
        )

    with st.expander("Row counts per table", expanded=False):
        st.json(bundle["row_counts"])
    with st.expander("recipe.yaml (reproducibility manifest)", expanded=False):
        st.code(dump_recipe(bundle["recipe"]), language="yaml")
    with st.expander("manifest.json — file integrity (SHA256)", expanded=False):
        st.json(bundle["manifest"]["files"])


def _default_settings(industry: str) -> dict:
    today = date.today()
    n_tx = 25_000
    settings = {
        "industry_for_defaults": industry,
        "org_slug": industry.split("-")[0],
        "org_name": None,
        "seed": 42,
        "start_date": date(today.year - 3, 1, 1),
        "end_date": today,
        "n_transactions": n_tx,
        "auto_scale": True,
    }
    settings.update(_derive_row_counts(n_tx))
    return settings


def _sync_settings_to_industry(settings: dict, industry: str) -> None:
    if settings.get("industry_for_defaults") != industry:
        settings["org_slug"] = industry.split("-")[0]
        settings["industry_for_defaults"] = industry


def _derive_row_counts(n_tx: int) -> dict[str, int]:
    return {k: max(_RATIO_FLOORS[k], int(n_tx * r)) for k, r in _DEFAULT_RATIOS.items()}


def _run_generation(industry: str, profile: dict, scenario_specs: list[dict], settings: dict) -> None:
    with st.spinner("Generating dataset bundle..."):
        cfg = GenerationConfig(
            seed=int(settings["seed"]),
            n_transactions=int(settings["n_transactions"]),
            n_contracts=int(settings["n_contracts"]),
            n_prs=int(settings["n_prs"]),
            n_pos=int(settings["n_pos"]),
            n_grs=int(settings["n_grs"]),
            n_invoices=int(settings["n_invoices"]),
            n_violations=int(settings["n_violations"]),
            org_slug=settings["org_slug"] or "demo",
            org_name=settings.get("org_name"),
            start_date=settings["start_date"],
            end_date=settings["end_date"],
        )
        dfs = generate(_profile_for_gen(profile), cfg)
        if scenario_specs:
            dfs = apply_scenarios(dfs, scenario_specs, seed=int(settings["seed"]))
        recipe = build_recipe(
            industry=industry,
            config=cfg.to_dict(),
            profile=profile,
            baseline_profile=PROFILES[industry],
            scenarios=scenario_specs,
        )
        tmp_path = Path("_tmp_bundle.zip")
        result = write_bundle(dfs, recipe, tmp_path)
        zip_bytes = tmp_path.read_bytes()
        tmp_path.unlink(missing_ok=True)
        st.session_state["last_bundle"] = {
            "name": result.bundle_name,
            "zip_bytes": zip_bytes,
            "row_counts": result.row_counts,
            "manifest": result.manifest,
            "recipe": recipe,
        }
    st.success(f"Bundle generated: {result.bundle_name} — see **Last Bundle** tab to download.")


def _profile_for_gen(profile: dict) -> dict:
    from copy import deepcopy
    p = deepcopy(profile)
    p = normalize_spend_share(p)
    p = normalize_seasonality(p)
    return p


if __name__ == "__main__":
    main()
