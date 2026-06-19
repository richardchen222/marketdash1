"""Market-wide reference data: sector ETFs and a movers watchlist.

Yahoo does not expose a clean "top gainers" endpoint via yfinance, so we derive
movers from a curated mega-cap watchlist and sector performance from the SPDR
sector ETFs. This keeps the feature fully reproducible from a single data source.
"""

from __future__ import annotations

import pandas as pd

from . import data_loader

try:
    import streamlit as st

    _cache_data = st.cache_data
except Exception:  # pragma: no cover
    def _cache_data(*dargs, **dkwargs):
        def _wrap(func):
            return func
        if dargs and callable(dargs[0]):
            return dargs[0]
        return _wrap


# SPDR sector ETFs — a standard proxy for U.S. sector performance.
SECTOR_ETFS = {
    "Technology": "XLK", "Financials": "XLF", "Healthcare": "XLV",
    "Energy": "XLE", "Industrials": "XLI", "Consumer Disc.": "XLY",
    "Consumer Staples": "XLP", "Utilities": "XLU", "Materials": "XLB",
    "Real Estate": "XLRE", "Communication": "XLC",
}

WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
             "AMD", "NFLX", "JPM", "V", "DIS", "BA", "INTC"]


@_cache_data(ttl=600, show_spinner=False)
def sector_performance() -> pd.DataFrame:
    """Return one-day percentage change for each sector ETF."""
    rows = []
    for name, etf in SECTOR_ETFS.items():
        hist = data_loader.fetch_history(etf, period="5d")
        if hist.empty or len(hist) < 2:
            continue
        change = (hist["Close"].iloc[-1] / hist["Close"].iloc[-2] - 1) * 100
        rows.append({"sector": name, "etf": etf, "change_pct": round(change, 2)})
    return pd.DataFrame(rows).sort_values("change_pct", ascending=False)


@_cache_data(ttl=600, show_spinner=False)
def movers() -> pd.DataFrame:
    """Return the watchlist with daily change and volume for ranking."""
    rows = []
    for tkr in WATCHLIST:
        hist = data_loader.fetch_history(tkr, period="5d")
        if hist.empty or len(hist) < 2:
            continue
        last, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
        rows.append({
            "ticker": tkr,
            "price": round(float(last), 2),
            "change_pct": round((last / prev - 1) * 100, 2),
            "volume": float(hist["Volume"].iloc[-1]),
        })
    return pd.DataFrame(rows)


def top_gainers(n: int = 5) -> pd.DataFrame:
    """Top ``n`` watchlist names by daily gain."""
    df = movers()
    return df.sort_values("change_pct", ascending=False).head(n) \
        if not df.empty else df


def top_losers(n: int = 5) -> pd.DataFrame:
    """Bottom ``n`` watchlist names by daily change."""
    df = movers()
    return df.sort_values("change_pct").head(n) if not df.empty else df


def most_active(n: int = 5) -> pd.DataFrame:
    """Top ``n`` watchlist names by traded volume."""
    df = movers()
    return df.sort_values("volume", ascending=False).head(n) \
        if not df.empty else df
