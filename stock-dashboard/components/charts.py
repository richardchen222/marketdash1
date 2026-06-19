"""Plotly chart builders.

Every function returns a configured ``go.Figure`` themed to the active palette.
Charts are intentionally free of business logic — they accept already-computed
frames from :mod:`utils` and focus solely on presentation: consistent fonts,
gradient accents, unified hover and disabled clutter.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import theme

_FONT = "Inter, sans-serif"


def _style(fig: go.Figure, dark: bool, height: int = 420) -> go.Figure:
    """Apply shared layout styling to any figure."""
    c = theme.palette(dark)
    fig.update_layout(
        template=theme.plotly_template(dark),
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(family=_FONT, color=c["text"], size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=c["border"]),
    )
    return fig


def candlestick(frame: pd.DataFrame, dark: bool,
                show_ma=(20, 50, 200), show_bbands: bool = False,
                signals: pd.DataFrame | None = None) -> go.Figure:
    """Candlestick + volume with overlaid moving averages and signals.

    Two stacked panels share an x-axis: price (with MAs / optional Bollinger
    Bands and buy/sell markers) on top and a volume histogram below. Native
    Plotly zoom, pan and a range-slider are enabled.
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.74, 0.26], vertical_spacing=0.04)

    fig.add_trace(go.Candlestick(
        x=frame.index, open=frame["Open"], high=frame["High"],
        low=frame["Low"], close=frame["Close"], name="Price",
        increasing_line_color=theme.POSITIVE,
        decreasing_line_color=theme.NEGATIVE,
    ), row=1, col=1)

    ma_colors = {20: theme.ACCENT_SOFT, 50: "#F59E0B", 200: "#0EA5E9"}
    for window in show_ma:
        col = f"MA{window}"
        if col in frame:
            fig.add_trace(go.Scatter(
                x=frame.index, y=frame[col], name=f"MA {window}",
                line=dict(width=1.6, color=ma_colors.get(window, "#888")),
            ), row=1, col=1)

    if show_bbands and {"BB_UPPER", "BB_LOWER"}.issubset(frame.columns):
        fig.add_trace(go.Scatter(x=frame.index, y=frame["BB_UPPER"],
                                 name="BB Upper", line=dict(width=0.8,
                                 color=theme.ACCENT, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=frame.index, y=frame["BB_LOWER"],
                                 name="BB Lower", fill="tonexty",
                                 fillcolor="rgba(124,58,237,.08)",
                                 line=dict(width=0.8, color=theme.ACCENT,
                                 dash="dot")), row=1, col=1)

    if signals is not None and not signals.empty:
        buys = signals[signals["type"] == "buy"]
        sells = signals[signals["type"] == "sell"]
        fig.add_trace(go.Scatter(x=buys["date"], y=buys["price"], mode="markers",
                                 name="Buy", marker=dict(symbol="triangle-up",
                                 size=12, color=theme.POSITIVE)), row=1, col=1)
        fig.add_trace(go.Scatter(x=sells["date"], y=sells["price"], mode="markers",
                                 name="Sell", marker=dict(symbol="triangle-down",
                                 size=12, color=theme.NEGATIVE)), row=1, col=1)

    vol_colors = np.where(frame["Close"] >= frame["Open"],
                          theme.POSITIVE, theme.NEGATIVE)
    fig.add_trace(go.Bar(x=frame.index, y=frame["Volume"], name="Volume",
                         marker_color=vol_colors, opacity=0.5), row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False)
    _style(fig, dark, height=560)
    fig.update_yaxes(gridcolor=theme.palette(dark)["border"], row=2, col=1)
    return fig


def rsi_chart(frame: pd.DataFrame, dark: bool) -> go.Figure:
    """RSI line with shaded overbought (70) and oversold (30) zones."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frame.index, y=frame["RSI"], name="RSI",
                             line=dict(color=theme.ACCENT, width=1.8)))
    fig.add_hrect(y0=70, y1=100, fillcolor=theme.NEGATIVE, opacity=0.07,
                  line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor=theme.POSITIVE, opacity=0.07,
                  line_width=0)
    fig.add_hline(y=70, line=dict(color=theme.NEGATIVE, width=1, dash="dot"))
    fig.add_hline(y=30, line=dict(color=theme.POSITIVE, width=1, dash="dot"))
    fig.update_yaxes(range=[0, 100])
    return _style(fig, dark, height=240)


def macd_chart(frame: pd.DataFrame, dark: bool) -> go.Figure:
    """MACD line, signal line and a colored histogram."""
    fig = go.Figure()
    hist_colors = np.where(frame["MACD_HIST"] >= 0, theme.POSITIVE, theme.NEGATIVE)
    fig.add_trace(go.Bar(x=frame.index, y=frame["MACD_HIST"], name="Histogram",
                         marker_color=hist_colors, opacity=0.5))
    fig.add_trace(go.Scatter(x=frame.index, y=frame["MACD"], name="MACD",
                             line=dict(color=theme.ACCENT, width=1.8)))
    fig.add_trace(go.Scatter(x=frame.index, y=frame["MACD_SIGNAL"], name="Signal",
                             line=dict(color="#F59E0B", width=1.4)))
    return _style(fig, dark, height=240)


def donut(allocation: pd.DataFrame, dark: bool) -> go.Figure:
    """Asset-allocation donut chart from a (ticker, value) frame."""
    palette_seq = ["#7C3AED", "#4F46E5", "#0EA5E9", "#06B6D4", "#8B5CF6",
                   "#F59E0B", "#EC4899", "#10B981"]
    fig = go.Figure(go.Pie(
        labels=allocation["ticker"], values=allocation["value"], hole=0.62,
        marker=dict(colors=palette_seq[:len(allocation)]),
        textinfo="label+percent", textposition="outside",
    ))
    fig.update_layout(showlegend=False)
    return _style(fig, dark, height=340)


def returns_distribution(returns: pd.Series, dark: bool) -> go.Figure:
    """Histogram of daily returns with a mean reference line."""
    fig = go.Figure(go.Histogram(x=returns * 100, nbinsx=60,
                                 marker_color=theme.ACCENT_SOFT, opacity=0.8,
                                 name="Daily returns"))
    fig.add_vline(x=float(returns.mean() * 100), line=dict(color=theme.NEGATIVE,
                  width=1.5, dash="dash"))
    fig.update_xaxes(title_text="Daily return (%)")
    return _style(fig, dark, height=320)


def correlation_heatmap(corr: pd.DataFrame, dark: bool) -> go.Figure:
    """Correlation matrix rendered as a violet-scaled heatmap."""
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
        colorscale=[[0, theme.NEGATIVE], [0.5, "#F1F5F9"], [1, theme.ACCENT]],
        text=corr.round(2).values, texttemplate="%{text}",
        textfont=dict(size=11),
    ))
    return _style(fig, dark, height=420)


def benchmark_chart(asset_cum: pd.Series, bench_cum: pd.Series,
                    asset_name: str, bench_name: str, dark: bool) -> go.Figure:
    """Cumulative return of the asset vs a benchmark (both as %)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=asset_cum.index, y=asset_cum * 100,
                             name=asset_name,
                             line=dict(color=theme.ACCENT, width=2)))
    fig.add_trace(go.Scatter(x=bench_cum.index, y=bench_cum * 100,
                             name=bench_name,
                             line=dict(color="#94A3B8", width=1.6, dash="dot")))
    fig.update_yaxes(title_text="Cumulative return (%)")
    return _style(fig, dark, height=380)


def rolling_vol_chart(vol: pd.Series, dark: bool) -> go.Figure:
    """Filled area chart of rolling annualized volatility."""
    fig = go.Figure(go.Scatter(
        x=vol.index, y=vol, name="Rolling volatility", fill="tozeroy",
        line=dict(color=theme.ACCENT, width=1.8),
        fillcolor="rgba(124,58,237,.12)"))
    fig.update_yaxes(title_text="Annualized volatility (%)")
    return _style(fig, dark, height=320)


def cumulative_chart(cum: pd.Series, dark: bool) -> go.Figure:
    """Cumulative return area chart for a single asset."""
    color = theme.POSITIVE if cum.iloc[-1] >= 0 else theme.NEGATIVE
    fill = ("rgba(22,163,74,.10)" if cum.iloc[-1] >= 0
            else "rgba(220,38,38,.10)")
    fig = go.Figure(go.Scatter(x=cum.index, y=cum * 100, fill="tozeroy",
                               line=dict(color=color, width=2), fillcolor=fill,
                               name="Cumulative return"))
    fig.update_yaxes(title_text="Cumulative return (%)")
    return _style(fig, dark, height=320)


def sector_heatmap(sectors: pd.DataFrame, dark: bool) -> go.Figure:
    """Sector performance as a single-row diverging heatmap (% change)."""
    fig = go.Figure(go.Heatmap(
        z=[sectors["change_pct"].values], x=sectors["sector"].values, y=[""],
        colorscale=[[0, theme.NEGATIVE], [0.5, "#F8FAFC"], [1, theme.POSITIVE]],
        zmid=0, text=[sectors["change_pct"].round(2).values],
        texttemplate="%{text}%", textfont=dict(size=12),
        colorbar=dict(title="%"),
    ))
    return _style(fig, dark, height=180)


def gauge(score: int, label: str, dark: bool) -> go.Figure:
    """Fear & Greed style gauge from a 0–100 sentiment score."""
    color = (theme.POSITIVE if score >= 60 else theme.NEUTRAL if score >= 40
             else theme.NEGATIVE)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, title={"text": label},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 20], "color": "rgba(220,38,38,.18)"},
                {"range": [20, 40], "color": "rgba(220,38,38,.08)"},
                {"range": [40, 60], "color": "rgba(99,102,241,.10)"},
                {"range": [60, 80], "color": "rgba(22,163,74,.08)"},
                {"range": [80, 100], "color": "rgba(22,163,74,.18)"},
            ],
        },
    ))
    return _style(fig, dark, height=280)
