from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def benford(transactions: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if transactions.empty:
        fig.update_layout(title="Benford first-digit distribution", height=260, margin=dict(l=10, r=10, t=40, b=10))
        return fig

    amounts = pd.to_numeric(transactions["amount"], errors="coerce").dropna()
    amounts = amounts[amounts >= 1]
    if amounts.empty:
        fig.update_layout(title="Benford first-digit distribution", height=260, margin=dict(l=10, r=10, t=40, b=10))
        return fig

    firsts = amounts.astype(float).apply(_first_digit)
    observed = firsts.value_counts(normalize=True).reindex(range(1, 10), fill_value=0.0)
    expected = pd.Series({d: math.log10(1 + 1 / d) for d in range(1, 10)})

    x = list(range(1, 10))
    fig.add_bar(x=x, y=observed.values, name="Observed", marker_color="#4C78A8")
    fig.add_scatter(x=x, y=expected.values, name="Benford", mode="lines+markers",
                    line=dict(color="#F58518", width=2))
    fig.update_layout(
        title="Benford first-digit distribution",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(title="Leading digit", tickmode="array", tickvals=x),
        yaxis=dict(title="Share", tickformat=".0%"),
        height=260,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _first_digit(v: float) -> int:
    if v <= 0:
        return 0
    while v >= 10:
        v /= 10
    while v < 1:
        v *= 10
    return int(v)
