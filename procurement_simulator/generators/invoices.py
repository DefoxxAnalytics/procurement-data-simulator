from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from procurement_simulator.generators.base import invoice_id

_MATCH_STATUSES = ["3way_matched", "2way_matched", "exception", "unmatched"]
_MATCH_P = np.array([0.55, 0.15, 0.20, 0.10])
_EXC_TYPES = ["price_variance", "quantity_variance", "missing_gr", "no_po", "duplicate", "other"]
_EXC_P = np.array([0.35, 0.25, 0.15, 0.10, 0.05, 0.10])
_STATUS_MAP = {
    "3way_matched": "approved",
    "2way_matched": "matched",
    "exception": "exception",
    "unmatched": "pending_match",
}


def generate_invoices(
    org_slug: str,
    profile: dict,
    pos_df: pd.DataFrame,
    grs_df: pd.DataFrame,
    n_invoices: int,
    today,
    rng: np.random.Generator,
) -> pd.DataFrame:
    if pos_df.empty or grs_df.empty:
        return pd.DataFrame()

    grs_by_po = {row["po_id"]: row for _, row in grs_df.iterrows()}
    pos_with_grs = pos_df[pos_df["po_id"].isin(grs_by_po.keys())].copy()
    if pos_with_grs.empty:
        return pd.DataFrame()
    pos_with_grs = pos_with_grs.sample(frac=1, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)
    target = pos_with_grs.head(n_invoices)

    payment_terms = profile["payment_terms"]

    rows = []
    for i in range(len(target)):
        po = target.iloc[i]
        gr = grs_by_po[po["po_id"]]

        invoice_date = gr["received_date"] + timedelta(days=int(rng.integers(0, 15)))
        if invoice_date > today:
            invoice_date = today

        term = payment_terms[int(rng.integers(0, len(payment_terms)))]
        term_label, term_days = term

        received_date = invoice_date + timedelta(days=int(rng.integers(0, 4)))
        if received_date > today:
            received_date = today
        due_date = received_date + timedelta(days=int(term_days))
        days_out = (today - invoice_date).days

        variance = round(float(rng.uniform(0.97, 1.06)), 4)
        invoice_amount = round(float(po["total_amount"]) * variance, 2)
        tax = round(invoice_amount * 0.08, 2)
        net = round(invoice_amount - tax, 2)

        match_status = str(rng.choice(_MATCH_STATUSES, p=_MATCH_P / _MATCH_P.sum()))
        has_exception = match_status == "exception"
        exception_type = str(rng.choice(_EXC_TYPES, p=_EXC_P / _EXC_P.sum())) if has_exception else ""
        exception_amount = round(abs(invoice_amount - float(po["total_amount"])), 2) if has_exception else None
        exception_resolved = bool(has_exception and float(rng.random()) < 0.25)

        paid_date = None
        if days_out < 30 and float(rng.random()) < 0.50 and match_status in {"3way_matched", "2way_matched"}:
            upper = max(int(term_days), int(days_out) + 1, 7)
            paid_date = received_date + timedelta(days=int(rng.integers(5, upper + 1)))

        if paid_date is not None:
            status = "paid"
        elif has_exception and not exception_resolved:
            status = "exception"
        elif has_exception and exception_resolved:
            status = "approved"
        else:
            status = _STATUS_MAP[match_status]

        approved_date = received_date + timedelta(days=int(rng.integers(1, 11))) if status in {"approved", "paid"} else None

        rows.append({
            "invoice_id": invoice_id(org_slug, invoice_date.year, i + 1),
            "invoice_number": invoice_id(org_slug, invoice_date.year, i + 1),
            "supplier_id": po["supplier_id"],
            "po_id": po["po_id"],
            "gr_id": gr["gr_id"],
            "invoice_amount": invoice_amount,
            "tax_amount": tax,
            "net_amount": net,
            "payment_terms": term_label,
            "payment_terms_days": int(term_days),
            "invoice_date": invoice_date,
            "received_date": received_date,
            "due_date": due_date,
            "approved_date": approved_date,
            "paid_date": paid_date,
            "status": status,
            "match_status": match_status,
            "has_exception": has_exception,
            "exception_type": exception_type,
            "exception_amount": exception_amount,
            "exception_resolved": exception_resolved,
            "exception_notes": "Auto-flagged during 3-way match" if has_exception else "",
        })
    return pd.DataFrame(rows)
