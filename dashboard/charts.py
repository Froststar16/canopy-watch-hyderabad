"""Plotly chart builders for ward trends and correlation analysis."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats


def ward_trend_chart(
    ndvi: pd.DataFrame, lst: pd.DataFrame, treecover: pd.DataFrame, ward_no: str
) -> go.Figure:
    ndvi_w = ndvi[ndvi["ward_no"] == ward_no].sort_values("year")
    lst_w = lst[lst["ward_no"] == ward_no].sort_values("year")
    tc_w = treecover[treecover["ward_no"] == ward_no].sort_values("year")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ndvi_w["year"], y=ndvi_w["ndvi"], name="NDVI", yaxis="y1"))
    fig.add_trace(
        go.Scatter(x=tc_w["year"], y=tc_w["tree_prob"], name="Tree-cover probability", yaxis="y1")
    )
    fig.add_trace(go.Scatter(x=lst_w["year"], y=lst_w["lst_c"], name="LST (°C)", yaxis="y2"))

    fig.update_layout(
        title=f"Ward {ward_no} trends",
        yaxis=dict(title="NDVI / tree-cover prob (0–1)"),
        yaxis2=dict(title="LST (°C)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=-0.25),
        margin=dict(t=40, b=40),
    )
    return fig


def correlation_scatter(
    df: pd.DataFrame, x_col: str, y_col: str, x_label: str, y_label: str, title: str
) -> go.Figure:
    clean = df[[x_col, y_col]].dropna()
    r, p = stats.pearsonr(clean[x_col], clean[y_col])

    fig = px.scatter(clean, x=x_col, y=y_col, labels={x_col: x_label, y_col: y_label})

    slope, intercept = np.polyfit(clean[x_col], clean[y_col], 1)
    x_range = np.linspace(clean[x_col].min(), clean[x_col].max(), 50)
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=slope * x_range + intercept,
            mode="lines",
            name="trend",
            line=dict(dash="dash"),
        )
    )

    fig.update_layout(
        title=f"{title}  (r={r:.2f}, p={p:.3f}, n={len(clean)})",
        margin=dict(t=50, b=40),
    )
    return fig
