from __future__ import annotations

import plotly.graph_objects as go


def spend_mix_donut(profile: dict) -> go.Figure:
    cats = profile["categories"]
    names = [c["name"] for c in cats]
    shares = [c["spend_share"] for c in cats]
    fig = go.Figure(data=[go.Pie(
        labels=names, values=shares, hole=0.55, sort=False,
        textinfo="label+percent", texttemplate="%{label}<br>%{percent}",
    )])
    fig.update_layout(
        title="Spend mix",
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        height=360,
    )
    return fig
