"""Portfolio page: holdings editor, allocation donut and risk metrics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import cards, charts, theme
from utils import analytics, data_loader, state

st.set_page_config(page_title="Lumina — Portfolio", page_icon="💼",
                   layout="wide")

_SAMPLE = pd.DataFrame({
    "ticker": ["AAPL", "MSFT", "NVDA", "AMZN"],
    "shares": [25, 15, 30, 10],
    "cost_basis": [165.0, 330.0, 90.0, 140.0],
})


def main() -> None:
    app = state.sidebar(active="Portfolio")
    theme.banner("Portfolio Analytics",
                 "Track allocation, P/L and risk-adjusted performance")

    with st.container(border=True):
        theme.section("Holdings", "Edit your positions")
        st.caption("Add or edit rows — values recalculate live. "
                   "Cost basis is the average per-share purchase price.")
        holdings = st.data_editor(
            _SAMPLE, num_rows="dynamic", use_container_width=True,
            hide_index=True, key="holdings_editor",
            column_config={
                "ticker": st.column_config.TextColumn("Ticker"),
                "shares": st.column_config.NumberColumn("Shares", min_value=0),
                "cost_basis": st.column_config.NumberColumn(
                    "Cost basis ($)", min_value=0.0, format="$%.2f"),
            })

    holdings = holdings.dropna(subset=["ticker"])
    holdings = holdings[holdings["ticker"].astype(str).str.strip() != ""]
    if holdings.empty:
        st.info("Add at least one holding to see analytics.")
        return

    # Current prices for each holding.
    price_map = {}
    for tkr in holdings["ticker"].astype(str).str.upper().unique():
        snap = data_loader.fetch_snapshot(tkr)
        if snap and snap.price:
            price_map[tkr] = snap.price

    summary = analytics.portfolio_summary(holdings, price_map)

    cols = st.columns(4)
    with cols[0]:
        cards.metric_card("Portfolio value",
                          cards.human_number(summary["total_value"], "$"))
    with cols[1]:
        pl = summary["total_pl"]
        cards.metric_card("Total P/L",
                          f"{cards.human_number(pl, '$')} "
                          f"({summary['total_pl_pct']:+.1f}%)")
    with cols[2]:
        cards.metric_card("Invested cost",
                          cards.human_number(summary["total_cost"], "$"))
    with cols[3]:
        cards.metric_card("Positions", str(len(holdings)))

    st.write("")
    left, right = st.columns([1, 1])

    with left:
        with st.container(border=True):
            theme.section("Allocation", "Weight by market value")
            if not summary["allocation"].empty:
                st.plotly_chart(charts.donut(summary["allocation"], app.dark),
                                use_container_width=True)

    with right:
        with st.container(border=True):
            theme.section("Risk", "Portfolio-weighted metrics vs S&P 500")
            # Build a value-weighted "portfolio close" series for risk math.
            tickers = tuple(holdings["ticker"].astype(str).str.upper())
            closes = data_loader.fetch_many_closes(tickers + ("SPY",),
                                                   period=app.period)
            if closes.empty or "SPY" not in closes:
                st.info("Not enough data to compute risk metrics.")
            else:
                weights = (summary["allocation"]
                           .set_index("ticker")["weight"] / 100)
                cols_present = [t for t in weights.index if t in closes.columns]
                port = (closes[cols_present] * weights[cols_present]).sum(axis=1)

                m = st.columns(2)
                with m[0]:
                    cards.metric_card("Sharpe ratio",
                                      f"{analytics.sharpe_ratio(port):.2f}")
                    cards.metric_card("Volatility (ann.)",
                                      f"{analytics.annualized_volatility(port):.1f}%")
                with m[1]:
                    cards.metric_card("Beta vs SPY",
                                      f"{analytics.beta(port, closes['SPY']):.2f}")
                    cards.metric_card("Max drawdown",
                                      f"{analytics.max_drawdown(port):.1f}%")

    st.caption("Educational tool only — not investment advice.")


if __name__ == "__main__":
    main()
