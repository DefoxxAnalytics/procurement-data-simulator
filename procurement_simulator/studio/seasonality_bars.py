from __future__ import annotations

import plotly.graph_objects as go

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def seasonality_bars(profile: dict) -> go.Figure:
    s = profile["seasonality"]
    fig = go.Figure()
    fig.add_bar(x=_MONTHS, y=s, marker_color="#4C78A8")
    fig.add_shape(type="line", x0=-0.5, x1=11.5, y0=1.0, y1=1.0,
                  line=dict(color="#F58518", dash="dash", width=1))
    fig.update_layout(
        title="Seasonality (monthly multiplier, mean ~1.0)",
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(title=None),
        xaxis=dict(title=None),
        height=240,
        showlegend=False,
    )
    return fig
