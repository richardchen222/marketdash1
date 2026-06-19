"""KPI cards, pills and number formatting helpers.

Thin wrappers over ``st.metric`` plus a few bespoke HTML cards so the top
section reads like a fintech terminal: an icon, a label, a big value and a
signed delta.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from . import theme


def human_number(value: Optional[float], prefix: str = "", suffix: str = "",
                 digits: int = 2) -> str:
    """Format large numbers with K/M/B/T suffixes; ``"—"`` for missing values."""
    if value is None:
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"

    for unit, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= scale:
            return f"{prefix}{value / scale:.{digits}f}{unit}{suffix}"
    return f"{prefix}{value:,.{digits}f}{suffix}"


def kpi(label: str, value: str, delta: Optional[str] = None,
        icon: str = "") -> None:
    """Render a single KPI as a native metric card with an optional icon."""
    st.metric(label=f"{icon}  {label}".strip(), value=value, delta=delta)


def kpi_row(snapshot, currency_symbol: str = "$") -> None:
    """Render the six headline KPIs for a stock snapshot in one row."""
    cols = st.columns(6)

    price = (human_number(snapshot.price, prefix=currency_symbol)
             if snapshot.price else "—")
    delta = (f"{snapshot.change_pct:+.2f}%"
             if snapshot.change_pct is not None else None)

    with cols[0]:
        kpi("Price", price, delta, "💵")
    with cols[1]:
        kpi("Day Change",
            human_number(snapshot.change, prefix=currency_symbol)
            if snapshot.change is not None else "—",
            delta, "📈")
    with cols[2]:
        kpi("Market Cap",
            human_number(snapshot.market_cap, prefix=currency_symbol, digits=2),
            icon="🏛️")
    with cols[3]:
        kpi("Volume", human_number(snapshot.volume, digits=1), icon="🔊")
    with cols[4]:
        kpi("P/E Ratio",
            f"{snapshot.pe_ratio:.1f}" if snapshot.pe_ratio else "—", icon="⚖️")
    with cols[5]:
        rng = "—"
        if snapshot.week52_low and snapshot.week52_high:
            rng = (f"{human_number(snapshot.week52_low, prefix=currency_symbol)}"
                   f" – {human_number(snapshot.week52_high, prefix=currency_symbol)}")
        kpi("52-Week Range", rng, icon="📐")


def pill(text: str, tone: str = "neu") -> str:
    """Return HTML for a colored status pill (``pos``/``neg``/``neu``)."""
    cls = {"positive": "pill-pos", "negative": "pill-neg"}.get(tone, "pill-neu")
    cls = {"pos": "pill-pos", "neg": "pill-neg", "neu": "pill-neu"}.get(tone, cls)
    return f"<span class='pill {cls}'>{text}</span>"


def metric_card(label: str, value: str, helptext: str = "") -> None:
    """A compact metric used in the analytics grids (no delta)."""
    st.metric(label=label, value=value, help=helptext or None)
