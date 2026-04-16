from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def category_mix(transactions: pd.DataFrame, categories: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if transactions.empty or categories.empty:
        fig.update_layout(title="Category mix vs target", height=260, margin=dict(l=10, r=10, t=40, b=10))
        return fig

    actual = (
        transactions.groupby("category_id")["amount"].sum().rename("actual")
    )
    total = actual.sum() or 1.0
    actual_share = actual / total
    merged = categories.set_index("category_id")[["name", "spend_share"]].join(
        actual_share.to_frame()
    ).reset_index()
    merged["actual"] = merged["actual"].fillna(0.0)
    merged = merged.sort_values("spend_share", ascending=False)

    fig.add_bar(x=merged["name"], y=merged["spend_share"], name="Target", marker_color="#B0B0B0")
    fig.add_bar(x=merged["name"], y=merged["actual"], name="Actual", marker_color="#4C78A8")
    fig.update_layout(
        title="Category mix: target vs actual",
        barmode="group",
        margin=dict(l=10, r=10, t=40, b=80),
        xaxis=dict(tickangle=-45),
        yaxis=dict(tickformat=".0%"),
        height=260,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
