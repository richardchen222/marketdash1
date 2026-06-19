"""Technical Analysis page: RSI, MACD, Bollinger Bands and signals."""

from __future__ import annotations

import streamlit as st

from components import cards, charts, theme
from utils import data_loader, indicators, state

st.set_page_config(page_title="Lumina — Technical Analysis", page_icon="📈",
                   layout="wide")


def main() -> None:
    app = state.sidebar(active="Technical Analysis")
    theme.banner("Technical Analysis",
                 f"Momentum & volatility indicators for {app.ticker}")

    frame = indicators.enrich(
        data_loader.fetch_history(app.ticker, period=app.period))
    if frame.empty:
        st.warning("No price history available.")
        return

    # Indicator summary KPIs
    rsi_now = frame["RSI"].iloc[-1]
    macd_now = frame["MACD"].iloc[-1]
    sig_now = frame["MACD_SIGNAL"].iloc[-1]
    bb_pos = ((frame["Close"].iloc[-1] - frame["BB_LOWER"].iloc[-1]) /
              (frame["BB_UPPER"].iloc[-1] - frame["BB_LOWER"].iloc[-1]) * 100)

    cols = st.columns(4)
    with cols[0]:
        cards.metric_card("RSI (14)", f"{rsi_now:.0f}",
                          "Overbought >70, oversold <30")
    with cols[1]:
        cards.metric_card("MACD posture",
                          "Bullish" if macd_now > sig_now else "Bearish")
    with cols[2]:
        cards.metric_card("Bollinger %B", f"{bb_pos:.0f}%",
                          "Position within the bands")
    with cols[3]:
        cards.metric_card("Trend", indicators.trend_label(frame))

    st.write("")
    with st.container(border=True):
        theme.section("Overlay", "Price with Bollinger Bands & signals")
        sigs = indicators.signal_crossovers(frame)
        st.plotly_chart(
            charts.candlestick(frame, app.dark, show_ma=(20, 50),
                               show_bbands=True, signals=sigs),
            use_container_width=True, config={"scrollZoom": True})

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            theme.section("Oscillator", "Relative Strength Index")
            st.plotly_chart(charts.rsi_chart(frame, app.dark),
                            use_container_width=True)
    with c2:
        with st.container(border=True):
            theme.section("Oscillator", "MACD")
            st.plotly_chart(charts.macd_chart(frame, app.dark),
                            use_container_width=True)

    if not sigs.empty:
        with st.container(border=True):
            theme.section("Signals", "Recent MA crossovers")
            display = sigs.tail(8).copy()
            display["date"] = display["date"].dt.strftime("%b %d, %Y")
            display["price"] = display["price"].round(2)
            display["type"] = display["type"].str.upper()
            st.dataframe(display.rename(columns={
                "date": "Date", "price": "Price", "type": "Signal"}),
                use_container_width=True, hide_index=True)

    st.caption("Indicators are computed from historical prices and are for "
               "educational purposes only — not investment advice.")


if __name__ == "__main__":
    main()
