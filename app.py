"""Lumina Markets — Overview page (application entry point).

Run with: ``streamlit run app.py``

This page renders the headline KPIs and the primary candlestick/volume chart.
The remaining sections live as multipage views under ``pages/`` and share global
state (ticker, period, theme) via :mod:`utils.state`.
"""

from __future__ import annotations

import streamlit as st

from components import cards, charts, theme
from utils import data_loader, indicators, insights, state

st.set_page_config(page_title="Lumina Markets — Overview", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")


def main() -> None:
    app = state.sidebar(active="Overview")

    snapshot = data_loader.fetch_snapshot(app.ticker)
    if snapshot is None:
        theme.banner("Symbol not found",
                     f"Couldn't load data for '{app.ticker}'.")
        st.error("Check the ticker symbol and try again. "
                 "Example valid symbols: AAPL, MSFT, TSLA, NVDA.")
        return

    theme.banner(
        f"{snapshot.name} ({snapshot.ticker})",
        f"{snapshot.sector or 'Equity'} · {snapshot.currency} · "
        f"Live overview & technicals",
    )

    # --- Headline KPIs ----------------------------------------------------
    cards.kpi_row(snapshot)
    st.write("")

    history = indicators.enrich(
        data_loader.fetch_history(app.ticker, period=app.period))
    if history.empty:
        st.warning("No price history available for the selected period.")
        return

    # --- Primary chart ----------------------------------------------------
    left, right = st.columns([3, 1])

    with left:
        with st.container(border=True):
            theme.section("Price Action", "Candlestick & Volume")
            ctrls = st.columns(4)
            ma20 = ctrls[0].checkbox("MA 20", True)
            ma50 = ctrls[1].checkbox("MA 50", True)
            ma200 = ctrls[2].checkbox("MA 200", True)
            bb = ctrls[3].checkbox("Bollinger", False)

            mas = tuple(w for w, on in
                        ((20, ma20), (50, ma50), (200, ma200)) if on)
            sigs = indicators.signal_crossovers(history)
            fig = charts.candlestick(history, app.dark, show_ma=mas,
                                     show_bbands=bb, signals=sigs)
            st.plotly_chart(fig, use_container_width=True,
                            config={"scrollZoom": True})

    with right:
        with st.container(border=True):
            theme.section("Snapshot", "At a glance")
            trend = indicators.trend_label(history)
            tone = ("pos" if "Up" in trend else "neg" if "Down" in trend
                    else "neu")
            st.markdown(cards.pill(trend, tone), unsafe_allow_html=True)
            st.write("")

            score, label = insights.sentiment_score(history)
            cards.metric_card("Sentiment score", f"{score}/100", label)

            rsi_now = history["RSI"].iloc[-1]
            cards.metric_card("RSI (14)", f"{rsi_now:.0f}")

            week_perf = (history["Close"].iloc[-1] /
                         history["Close"].iloc[0] - 1) * 100
            cards.metric_card("Period return", f"{week_perf:+.2f}%")

        with st.container(border=True):
            theme.section("Quick insights", "Generated")
            for item in insights.generate(history)[:3]:
                st.markdown(
                    f"<div class='insight'><div class='ic'>{item.icon}</div>"
                    f"<div><p class='tt'>{item.title}</p>"
                    f"<p class='dd'>{item.detail}</p></div></div>",
                    unsafe_allow_html=True)

    st.caption("Explore deeper analysis using the navigation in the sidebar → "
               "Technical Analysis, Portfolio, Market Intelligence, "
               "Data Analytics and AI Insights.")


if __name__ == "__main__":
    main()
