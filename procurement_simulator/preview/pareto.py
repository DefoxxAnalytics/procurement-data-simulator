from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def supplier_pareto(transactions: pd.DataFrame, suppliers: pd.DataFrame, top_n: int = 20) -> go.Figure:
    if transactions.empty:
        return _empty("Supplier spend Pareto")

    spend = (
        transactions.groupby("supplier_id")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    top = spend.head(top_n)
    names_map = dict(zip(suppliers["supplier_id"], suppliers["name"])) if not suppliers.empty else {}
    labels = [names_map.get(i, i) for i in top.index]
    cum = top.cumsum() / spend.sum() * 100

    fig = go.Figure()
    fig.add_bar(x=labels, y=top.values, name="Spend", marker_color="#4C78A8")
    fig.add_scatter(x=labels, y=cum.values, name="Cumulative %", yaxis="y2",
                    line=dict(color="#F58518", width=2))
    fig.update_layout(
        title="Supplier spend Pareto (top 20)",
        margin=dict(l=10, r=10, t=40, b=80),
        xaxis=dict(tickangle=-45),
        yaxis=dict(title="Spend"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]),
        showlegend=False,
        height=260,
    )
    return fig


def _empty(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, height=260, margin=dict(l=10, r=10, t=40, b=10))
    return fig
