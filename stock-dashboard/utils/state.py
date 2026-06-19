"""Shared application state and the sidebar control panel.

Centralizes session-state defaults and the sidebar so every page renders the
same navigation, theme toggle and global ticker/period controls. Pages call
:func:`sidebar` first, then read the returned :class:`AppState`.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from components import theme
from utils import data_loader


@dataclass
class AppState:
    """Resolved global controls for the current render."""

    ticker: str
    period: str
    dark: bool


_DEFAULTS = {"ticker": "AAPL", "period": "1y", "dark": False}

NAV = {
    "Overview": "app.py",
    "Technical Analysis": "pages/1_Technical_Analysis.py",
    "Portfolio": "pages/2_Portfolio.py",
    "Market Intelligence": "pages/3_Market_Intelligence.py",
    "Data Analytics": "pages/4_Data_Analytics.py",
    "AI Insights": "pages/5_AI_Insights.py",
}


def init_state() -> None:
    """Seed session state with defaults exactly once."""
    for key, value in _DEFAULTS.items():
        st.session_state.setdefault(key, value)


def sidebar(active: str) -> AppState:
    """Render the sidebar and return the resolved :class:`AppState`.

    ``active`` is the label of the current page so navigation can highlight it.
    """
    init_state()

    with st.sidebar:
        st.markdown("## 📊 **Lumina** Markets")
        st.caption("Equity analytics terminal")

        st.markdown("##### Navigation")
        for label, path in NAV.items():
            disabled = label == active
            st.page_link(path, label=label, disabled=disabled)

        st.divider()
        st.markdown("##### Global controls")
        ticker = st.text_input("Ticker symbol",
                               value=st.session_state["ticker"]).upper().strip()
        period = st.select_slider("Time period",
                                  options=data_loader.VALID_PERIODS,
                                  value=st.session_state["period"])
        dark = st.toggle("🌙 Dark mode", value=st.session_state["dark"])

        st.session_state.update(ticker=ticker or "AAPL",
                                period=period, dark=dark)

        st.divider()
        st.caption("Data: Yahoo Finance via yfinance. "
                   "For educational use only — not investment advice.")

    theme.inject(dark=st.session_state["dark"])
    return AppState(ticker=st.session_state["ticker"],
                    period=st.session_state["period"],
                    dark=st.session_state["dark"])
