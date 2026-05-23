from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_dark"
COLOR_SEQ = ["#4ee28a", "#f5c66b", "#66d9ef", "#ff7b7b", "#b48cff"]


def apply_chart_style(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(
        template=TEMPLATE,
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(3,18,11,.35)",
        font={"color": "#eef9f1"},
        margin=dict(l=20, r=20, t=55, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)")
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    if df.empty or x not in df.columns or y not in df.columns:
        return apply_chart_style(go.Figure(), title)
    fig = px.bar(df, x=x, y=y, color=color, color_discrete_sequence=COLOR_SEQ)
    return apply_chart_style(fig, title)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    if df.empty or x not in df.columns or y not in df.columns:
        return apply_chart_style(go.Figure(), title)
    fig = px.line(df, x=x, y=y, color=color, markers=True, color_discrete_sequence=COLOR_SEQ)
    return apply_chart_style(fig, title)


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str):
    if df.empty or names not in df.columns or values not in df.columns:
        return apply_chart_style(go.Figure(), title)
    fig = px.pie(df, names=names, values=values, hole=.45, color_discrete_sequence=COLOR_SEQ)
    return apply_chart_style(fig, title)


def radar_chart(labels: list[str], values_a: list[float], name_a: str, values_b: list[float] | None = None, name_b: str | None = None, title: str = "Radar"):
    fig = go.Figure()
    labels_closed = labels + [labels[0]]
    fig.add_trace(go.Scatterpolar(r=values_a + [values_a[0]], theta=labels_closed, fill="toself", name=name_a))
    if values_b is not None and name_b:
        fig.add_trace(go.Scatterpolar(r=values_b + [values_b[0]], theta=labels_closed, fill="toself", name=name_b))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    return apply_chart_style(fig, title)
