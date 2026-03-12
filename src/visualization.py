"""
visualization.py — Automatic chart generation based on DataFrame structure.

Strategy:
  - date/time column + numeric → Line chart
  - 1 categorical + 1 numeric → Bar chart
  - 2+ numerics, no categories → Scatter / multi-line
  - single numeric → Histogram
  - fallback → Table (no chart)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def _detect_date_cols(df: pd.DataFrame) -> list[str]:
    date_cols = []
    for col in df.columns:
        if df[col].dtype == object:
            try:
                pd.to_datetime(df[col].dropna().head(5))
                date_cols.append(col)
            except Exception:
                pass
        elif "date" in col.lower() or "time" in col.lower() or "month" in col.lower() or "year" in col.lower():
            date_cols.append(col)
    return date_cols


def _detect_cat_cols(df: pd.DataFrame) -> list[str]:
    return [
        col for col in df.columns
        if df[col].dtype == object or df[col].nunique() < 20
        and col not in _detect_date_cols(df)
    ]


def _detect_num_cols(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]


def auto_visualize(df: pd.DataFrame, title: str = "Query Result") -> Optional[go.Figure]:
    """
    Automatically generate a Plotly figure based on DataFrame structure.
    Returns None if no meaningful chart can be generated.
    """
    if df is None or df.empty or len(df.columns) < 1:
        return None

    date_cols = _detect_date_cols(df)
    num_cols = _detect_num_cols(df)
    cat_cols = [c for c in _detect_cat_cols(df) if c not in date_cols]

    # ── Case 1: Time series → Line chart ─────────────────────────────────────
    if date_cols and num_cols:
        x_col = date_cols[0]
        y_col = num_cols[0]
        color_col = cat_cols[0] if cat_cols else None

        df_plot = df.copy()
        df_plot[x_col] = pd.to_datetime(df_plot[x_col], errors="coerce")
        df_plot = df_plot.sort_values(x_col)

        fig = px.line(
            df_plot, x=x_col, y=y_col,
            color=color_col,
            title=title,
            markers=True,
        )
        fig.update_layout(template="plotly_white")
        return fig

    # ── Case 2: Category + numeric → Bar chart ───────────────────────────────
    if cat_cols and num_cols:
        x_col = cat_cols[0]
        y_col = num_cols[0]
        color_col = cat_cols[1] if len(cat_cols) > 1 else None

        fig = px.bar(
            df.sort_values(y_col, ascending=False),
            x=x_col, y=y_col,
            color=color_col,
            title=title,
            text_auto=".2s",
        )
        fig.update_layout(template="plotly_white", xaxis_tickangle=-30)
        return fig

    # ── Case 3: Multiple numerics → Scatter ──────────────────────────────────
    if len(num_cols) >= 2:
        fig = px.scatter(
            df, x=num_cols[0], y=num_cols[1],
            title=title,
            trendline="ols" if len(df) > 5 else None,
        )
        fig.update_layout(template="plotly_white")
        return fig

    # ── Case 4: Single numeric → Histogram ───────────────────────────────────
    if len(num_cols) == 1:
        fig = px.histogram(
            df, x=num_cols[0],
            title=title,
            nbins=20,
        )
        fig.update_layout(template="plotly_white")
        return fig

    return None


def fig_to_json(fig: go.Figure) -> str:
    """Serialize Plotly figure to JSON string for API transport."""
    return fig.to_json() if fig else ""