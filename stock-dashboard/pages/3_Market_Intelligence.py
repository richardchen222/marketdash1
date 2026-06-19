"""Market Intelligence page: news, sentiment gauge, sectors and movers."""

from __future__ import annotations

import streamlit as st

from components import cards, charts, theme
from utils import data_loader, indicators, insights, market, state

st.set_page_config(page_title="Lumina — Market Intelligence", page_icon="🌐",
                   layout="wide")


def _movers_table(df, label_col="change_pct", suffix="%"):
    """Render a compact movers table with signed change coloring."""
    if df.empty:
        st.caption("No data available.")
        return
    show = df.copy()
    show["change_pct"] = show["change_pct"].map(lambda v: f"{v:+.2f}%")
    show["price"] = show["price"].map(lambda v: f"${v:,.2f}")
    st.dataframe(show.rename(columns={
        "ticker": "Ticker", "price": "Price", "change_pct": "Change",
        "volume": "Volume"}), use_container_width=True, hide_index=True)


def main() -> None:
    app = state.sidebar(active="Market Intelligence")
    theme.banner("Market Intelligence",
                 "News, sentiment, sector rotation and movers")

    top = st.columns([1, 1])

    with top[0]:
        with st.container(border=True):
            theme.section("Sentiment", f"Fear & Greed — {app.ticker}")
            frame = indicators.enrich(
                data_loader.fetch_history(app.ticker, period=app.period))
            score, label = insights.sentiment_score(frame)
            st.plotly_chart(charts.gauge(score, label, app.dark),
                            use_container_width=True)

    with top[1]:
        with st.container(border=True):
            theme.section("Headlines", f"Latest news — {app.ticker}")
            news = data_loader.fetch_news(app.ticker)
            if not news:
                st.caption("No recent headlines found for this symbol.")
            for item in news:
                link = item["link"] or "#"
                st.markdown(
                    f"<div class='news-item'><a href='{link}' target='_blank'>"
                    f"{item['title']}</a><div class='news-meta'>"
                    f"{item['publisher']} · {item['published']}</div></div>",
                    unsafe_allow_html=True)

    with st.container(border=True):
        theme.section("Rotation", "Sector performance (1-day)")
        sectors = market.sector_performance()
        if sectors.empty:
            st.caption("Sector data unavailable right now.")
        else:
            st.plotly_chart(charts.sector_heatmap(sectors, app.dark),
                            use_container_width=True)

    g, l, a = st.columns(3)
    with g:
        with st.container(border=True):
            theme.section("Movers", "🟢 Top gainers")
            _movers_table(market.top_gainers())
    with l:
        with st.container(border=True):
            theme.section("Movers", "🔴 Top losers")
            _movers_table(market.top_losers())
    with a:
        with st.container(border=True):
            theme.section("Movers", "🔥 Most active")
            _movers_table(market.most_active())

    st.caption("Movers are derived from a curated mega-cap watchlist. "
               "Educational tool only — not investment advice.")


if __name__ == "__main__":
    main()
