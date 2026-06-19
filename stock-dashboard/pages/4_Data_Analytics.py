"""Data Analytics page: distributions, correlations, benchmarking, volatility."""

from __future__ import annotations

import streamlit as st

from components import cards, charts, theme
from utils import analytics, data_loader, state

st.set_page_config(page_title="Lumina — Data Analytics", page_icon="🧮",
                   layout="wide")

_DEFAULT_BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]


def main() -> None:
    app = state.sidebar(active="Data Analytics")
    theme.banner("Data Analytics",
                 "Statistical view of returns, risk and correlation")

    close = data_loader.fetch_history(app.ticker, period=app.period)
    if close.empty:
        st.warning("No price history available.")
        return
    close = close["Close"]
    returns = analytics.daily_returns(close)

    # Summary statistics
    cols = st.columns(4)
    with cols[0]:
        cards.metric_card("Mean daily return", f"{returns.mean() * 100:+.3f}%")
    with cols[1]:
        cards.metric_card("Volatility (ann.)",
                          f"{analytics.annualized_volatility(close):.1f}%")
    with cols[2]:
        cards.metric_card("Sharpe ratio",
                          f"{analytics.sharpe_ratio(close):.2f}")
    with cols[3]:
        cards.metric_card("Max drawdown",
                          f"{analytics.max_drawdown(close):.1f}%")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            theme.section("Distribution", "Daily returns histogram")
            st.plotly_chart(charts.returns_distribution(returns, app.dark),
                            use_container_width=True)
    with c2:
        with st.container(border=True):
            theme.section("Risk over time", "Rolling 21-day volatility")
            st.plotly_chart(
                charts.rolling_vol_chart(
                    analytics.rolling_volatility(close).dropna(), app.dark),
                use_container_width=True)

    with st.container(border=True):
        theme.section("Benchmarking", f"{app.ticker} vs S&P 500 (SPY)")
        spy = data_loader.fetch_history("SPY", period=app.period)
        if spy.empty:
            st.caption("Benchmark data unavailable.")
        else:
            asset_cum = analytics.cumulative_returns(close)
            bench_cum = analytics.cumulative_returns(spy["Close"])
            st.plotly_chart(
                charts.benchmark_chart(asset_cum, bench_cum, app.ticker,
                                       "S&P 500", app.dark),
                use_container_width=True)
            b = analytics.beta(close, spy["Close"])
            st.markdown(cards.pill(f"Beta vs S&P 500: {b:.2f}", "neu"),
                        unsafe_allow_html=True)

    with st.container(border=True):
        theme.section("Correlation", "Return correlation across a basket")
        basket = _DEFAULT_BASKET.copy()
        if app.ticker not in basket:
            basket = [app.ticker] + basket[:-1]
        chosen = st.multiselect("Basket", options=sorted(set(
            basket + ["TSLA", "META", "SPY", "JPM"])), default=basket)
        if len(chosen) >= 2:
            closes = data_loader.fetch_many_closes(tuple(chosen),
                                                   period=app.period)
            corr = analytics.correlation_matrix(closes)
            if not corr.empty:
                st.plotly_chart(charts.correlation_heatmap(corr, app.dark),
                                use_container_width=True)
        else:
            st.caption("Select at least two symbols to compute correlations.")

    st.caption("Educational tool only — not investment advice.")


if __name__ == "__main__":
    main()
