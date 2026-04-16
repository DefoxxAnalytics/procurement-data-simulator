from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def monthly_trend(transactions: pd.DataFrame) -> go.Figure:
    if transactions.empty:
        fig = go.Figure()
        fig.update_layout(title="Monthly spend trend", height=260, margin=dict(l=10, r=10, t=40, b=10))
        return fig

    df = transactions.copy()
    df["date"] = pd.to_datetime(df["date"])
    monthly = df.groupby(pd.Grouper(key="date", freq="MS"))["amount"].sum().reset_index()

    fig = go.Figure()
    fig.add_scatter(
        x=monthly["date"], y=monthly["amount"],
        mode="lines+markers", line=dict(color="#4C78A8", width=2),
        marker=dict(size=4),
    )
    fig.update_layout(
        title="Monthly spend trend",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(title=None),
        yaxis=dict(title="Spend"),
        height=260,
    )
    return fig
