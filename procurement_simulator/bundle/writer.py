from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from procurement_simulator.bundle.data_dictionary import SCHEMA, render_data_dictionary
from procurement_simulator.bundle.readme_writer import render_readme
from procurement_simulator.bundle.recipe import GENERATOR_VERSION, dump_recipe
from procurement_simulator.bundle.sample_queries import SAMPLE_QUERIES

_TABLE_ORDER = [
    "categories",
    "suppliers",
    "contracts",
    "contract_categories",
    "policies",
    "transactions",
    "policy_violations",
    "purchase_requisitions",
    "purchase_orders",
    "goods_receipts",
    "invoices",
]

_FK_CONSTRAINTS: dict[str, list[tuple[str, str, str]]] = {
    "transactions": [
        ("category_id", "categories", "category_id"),
        ("supplier_id", "suppliers", "supplier_id"),
    ],
    "contracts": [
        ("supplier_id", "suppliers", "supplier_id"),
    ],
    "contract_categories": [
        ("contract_id", "contracts", "contract_id"),
        ("category_id", "categories", "category_id"),
    ],
    "policy_violations": [
        ("transaction_id", "transactions", "transaction_id"),
        ("policy_id", "policies", "policy_id"),
    ],
    "purchase_requisitions": [
        ("supplier_suggested_id", "suppliers", "supplier_id"),
        ("category_id", "categories", "category_id"),
    ],
    "purchase_orders": [
        ("supplier_id", "suppliers", "supplier_id"),
        ("category_id", "categories", "category_id"),
        ("contract_id", "contracts", "contract_id"),
        ("pr_id", "purchase_requisitions", "pr_id"),
    ],
    "goods_receipts": [
        ("po_id", "purchase_orders", "po_id"),
    ],
    "invoices": [
        ("supplier_id", "suppliers", "supplier_id"),
        ("po_id", "purchase_orders", "po_id"),
        ("gr_id", "goods_receipts", "gr_id"),
    ],
}

_PK_COLUMN: dict[str, str] = {
    "categories": "category_id",
    "suppliers": "supplier_id",
    "contracts": "contract_id",
    "policies": "policy_id",
    "transactions": "transaction_id",
    "policy_violations": "violation_id",
    "purchase_requisitions": "pr_id",
    "purchase_orders": "po_id",
    "goods_receipts": "gr_id",
    "invoices": "invoice_id",
}


@dataclass
class BundleResult:
    zip_path: Path
    bundle_name: str
    row_counts: dict[str, int]
    manifest: dict


def write_bundle(
    dfs: dict[str, pd.DataFrame],
    recipe: dict,
    out_path: str | Path,
    bundle_name: str | None = None,
) -> BundleResult:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    industry = recipe.get("industry", "dataset")
    scenario_names = [s.get("name", "?") for s in recipe.get("scenarios", [])]
    name = bundle_name or _default_name(industry, scenario_names)

    csv_bytes: dict[str, bytes] = {}
    row_counts: dict[str, int] = {}
    for table in _TABLE_ORDER:
        df = dfs.get(table)
        if df is None:
            df = pd.DataFrame()
        buf = io.StringIO()
        df.to_csv(buf, index=False, date_format="%Y-%m-%d")
        data = buf.getvalue().encode("utf-8")
        csv_bytes[table] = data
        row_counts[table] = len(df)

    xlsx_bytes = _build_xlsx(dfs)
    sqlite_bytes = _build_sqlite(dfs)
    recipe_text = dump_recipe(recipe).encode("utf-8")
    dictionary_text = render_data_dictionary().encode("utf-8")
    queries_text = SAMPLE_QUERIES.encode("utf-8")
    readme_text = render_readme(name, industry, row_counts, scenario_names).encode("utf-8")

    manifest = _build_manifest(
        bundle_name=name,
        industry=industry,
        row_counts=row_counts,
        files={
            **{f"data/{t}.csv": csv_bytes[t] for t in _TABLE_ORDER},
            "dataset.xlsx": xlsx_bytes,
            "dataset.sqlite": sqlite_bytes,
            "recipe.yaml": recipe_text,
            "data_dictionary.md": dictionary_text,
            "sample_queries.sql": queries_text,
            "README.md": readme_text,
        },
        scenario_names=scenario_names,
        seed=int(recipe.get("config", {}).get("seed", 0)),
    )
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for t in _TABLE_ORDER:
            zf.writestr(f"{name}/data/{t}.csv", csv_bytes[t])
        zf.writestr(f"{name}/dataset.xlsx", xlsx_bytes)
        zf.writestr(f"{name}/dataset.sqlite", sqlite_bytes)
        zf.writestr(f"{name}/recipe.yaml", recipe_text)
        zf.writestr(f"{name}/manifest.json", manifest_text)
        zf.writestr(f"{name}/data_dictionary.md", dictionary_text)
        zf.writestr(f"{name}/sample_queries.sql", queries_text)
        zf.writestr(f"{name}/README.md", readme_text)

    return BundleResult(zip_path=out_path, bundle_name=name, row_counts=row_counts, manifest=manifest)


def _default_name(industry: str, scenarios: list[str]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    scen = "with-" + "-".join(scenarios) if scenarios else "baseline"
    return f"{industry}-{scen}-{stamp}"


def _build_xlsx(dfs: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for t in _TABLE_ORDER:
            df = dfs.get(t)
            if df is None or df.empty:
                pd.DataFrame(columns=list(SCHEMA[t].keys()) if t in SCHEMA else []).to_excel(writer, sheet_name=t[:31], index=False)
            else:
                df.to_excel(writer, sheet_name=t[:31], index=False)
    return buf.getvalue()


def _build_sqlite(dfs: dict[str, pd.DataFrame]) -> bytes:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    for t in _TABLE_ORDER:
        df = dfs.get(t, pd.DataFrame())
        cur.execute(_build_create_table(t, df))

    for t in _TABLE_ORDER:
        df = dfs.get(t, pd.DataFrame())
        if df.empty:
            continue
        df_out = df.copy()
        for col in df_out.columns:
            if pd.api.types.is_datetime64_any_dtype(df_out[col]):
                df_out[col] = df_out[col].dt.strftime("%Y-%m-%d")
            elif df_out[col].dtype == "object" and any(isinstance(v, (date, datetime)) for v in df_out[col].dropna().head(5)):
                df_out[col] = df_out[col].map(lambda v: v.isoformat() if isinstance(v, (date, datetime)) else v)
        cols = list(df_out.columns)
        placeholders = ", ".join("?" * len(cols))
        sql = f'INSERT INTO {t} ({", ".join(cols)}) VALUES ({placeholders})'
        values = [
            tuple(None if (pd.isna(v) if not isinstance(v, (list, dict)) else False) else v for v in row)
            for row in df_out.itertuples(index=False, name=None)
        ]
        cur.executemany(sql, values)
    conn.commit()

    buf = io.BytesIO()
    for line in conn.iterdump():
        buf.write(f"{line}\n".encode("utf-8"))
    sql_dump = buf.getvalue()

    disk_buf = io.BytesIO()
    disk_conn = sqlite3.connect(":memory:")
    disk_conn.executescript(sql_dump.decode("utf-8"))
    disk_conn.commit()
    tmp_path = _write_sqlite_to_tempfile(disk_conn)
    disk_conn.close()
    conn.close()
    return tmp_path.read_bytes()


def _write_sqlite_to_tempfile(in_memory_conn: sqlite3.Connection) -> Path:
    import tempfile
    tmp = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    disk = sqlite3.connect(str(tmp))
    in_memory_conn.backup(disk)
    disk.close()
    return tmp


def _build_create_table(table: str, df: pd.DataFrame) -> str:
    cols = _column_types(table, df)
    pk = _PK_COLUMN.get(table)
    col_defs = []
    for col, sql_type in cols:
        suffix = " PRIMARY KEY" if col == pk else ""
        col_defs.append(f"  {col} {sql_type}{suffix}")
    fks = _FK_CONSTRAINTS.get(table, [])
    for col, ref_table, ref_col in fks:
        col_defs.append(f"  FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})")
    return f"CREATE TABLE {table} (\n" + ",\n".join(col_defs) + "\n);"


def _column_types(table: str, df: pd.DataFrame) -> list[tuple[str, str]]:
    schema = SCHEMA.get(table, {})
    columns = list(df.columns) if not df.empty else list(schema.keys())
    out: list[tuple[str, str]] = []
    for col in columns:
        dtype = df[col].dtype if not df.empty and col in df.columns else None
        sql_type = _infer_sql_type(col, dtype)
        out.append((col, sql_type))
    return out


def _infer_sql_type(col: str, dtype) -> str:
    if col.endswith("_id") or col in {"pr_number", "po_number", "gr_number", "invoice_number", "contract_number"}:
        return "TEXT"
    if col in {"is_named", "is_active", "is_contract_backed", "auto_renew", "is_resolved", "has_exception", "exception_resolved"}:
        return "INTEGER"
    if col.endswith("_date") or col == "date":
        return "TEXT"
    if col in {"amount", "total_amount", "tax_amount", "freight_amount", "original_amount",
               "estimated_amount", "total_value", "annual_value", "invoice_amount",
               "net_amount", "exception_amount", "amount_received",
               "quantity_ordered", "quantity_received", "quantity_accepted",
               "spend_share", "amount_mu", "amount_sigma"}:
        return "REAL"
    if col in {"renewal_notice_days", "payment_terms_days", "amendment_count"}:
        return "INTEGER"
    if dtype is not None:
        if pd.api.types.is_integer_dtype(dtype):
            return "INTEGER"
        if pd.api.types.is_float_dtype(dtype):
            return "REAL"
        if pd.api.types.is_bool_dtype(dtype):
            return "INTEGER"
    return "TEXT"


def _build_manifest(
    bundle_name: str,
    industry: str,
    row_counts: dict[str, int],
    files: dict[str, bytes],
    scenario_names: list[str],
    seed: int,
) -> dict:
    return {
        "bundle_name": bundle_name,
        "generator_version": GENERATOR_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "industry": industry,
        "seed": seed,
        "scenarios": scenario_names,
        "row_counts": row_counts,
        "files": {
            name: {
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in files.items()
        },
    }
