from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import GenerationConfig
from procurement_simulator.generators.categories import generate_categories
from procurement_simulator.generators.contracts import generate_contracts
from procurement_simulator.generators.goods_receipts import generate_grs
from procurement_simulator.generators.invoices import generate_invoices
from procurement_simulator.generators.policies import generate_policies
from procurement_simulator.generators.policy_violations import generate_policy_violations
from procurement_simulator.generators.purchase_orders import generate_pos
from procurement_simulator.generators.purchase_requisitions import generate_prs
from procurement_simulator.generators.suppliers import generate_suppliers
from procurement_simulator.generators.transactions import generate_transactions

__all__ = ["generate", "GenerationConfig"]


def generate(profile: dict, config: GenerationConfig | None = None) -> dict[str, pd.DataFrame]:
    cfg = config or GenerationConfig()
    rng = np.random.default_rng(cfg.seed)
    today = cfg.end_date

    categories_df = generate_categories(profile)
    name_to_cat_id = dict(zip(categories_df["name"], categories_df["category_id"]))

    suppliers_df, suppliers_by_cat = generate_suppliers(profile, rng)

    transactions_df = generate_transactions(
        profile=profile,
        suppliers_by_cat=suppliers_by_cat,
        n_transactions=cfg.n_transactions,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        rng=rng,
    )
    transactions_df["category_id"] = transactions_df["category"].map(name_to_cat_id)
    transactions_df = transactions_df[[
        "transaction_id", "date", "category_id", "supplier_id", "amount",
    ]]

    contracts_df, contract_categories_df = generate_contracts(
        org_slug=cfg.org_slug,
        suppliers_df=suppliers_df,
        categories_df=categories_df,
        transactions_df=transactions_df,
        n_contracts=cfg.n_contracts,
        today=today,
        rng=rng,
    )

    policies_df = generate_policies(profile)
    violations_df = generate_policy_violations(
        transactions_df=transactions_df,
        policies_df=policies_df,
        suppliers_df=suppliers_df,
        n_violations=cfg.n_violations,
        rng=rng,
    )

    prs_df = generate_prs(
        org_slug=cfg.org_slug,
        profile=profile,
        suppliers_df=suppliers_df,
        categories_df=categories_df,
        n_prs=cfg.n_prs,
        today=today,
        rng=rng,
    )
    pos_df, prs_df = generate_pos(
        org_slug=cfg.org_slug,
        suppliers_df=suppliers_df,
        categories_df=categories_df,
        contracts_df=contracts_df,
        prs_df=prs_df,
        n_pos=cfg.n_pos,
        today=today,
        rng=rng,
    )
    grs_df = generate_grs(
        org_slug=cfg.org_slug,
        pos_df=pos_df,
        n_grs=cfg.n_grs,
        today=today,
        rng=rng,
    )
    invoices_df = generate_invoices(
        org_slug=cfg.org_slug,
        profile=profile,
        pos_df=pos_df,
        grs_df=grs_df,
        n_invoices=cfg.n_invoices,
        today=today,
        rng=rng,
    )

    return {
        "categories": categories_df,
        "suppliers": suppliers_df,
        "transactions": transactions_df,
        "contracts": contracts_df,
        "contract_categories": contract_categories_df,
        "policies": policies_df,
        "policy_violations": violations_df,
        "purchase_requisitions": prs_df,
        "purchase_orders": pos_df,
        "goods_receipts": grs_df,
        "invoices": invoices_df,
    }
