"""Data access layer.

All network access to Yahoo Finance is funneled through this module so that
caching, retries and error handling live in exactly one place. The UI never
talks to yfinance directly — it asks this module for clean, typed DataFrames.

Streamlit's caching decorators are imported lazily so that the functions remain
importable (and unit-testable) outside of a Streamlit runtime.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import yfinance as yf

try:
    import streamlit as st

    _cache_data = st.cache_data
except Exception:  # pragma: no cover - allows import outside Streamlit
    def _cache_data(*dargs, **dkwargs):
        def _wrap(func):
            return func

        # Support both @_cache_data and @_cache_data(ttl=...)
        if dargs and callable(dargs[0]):
            return dargs[0]
        return _wrap


# Period -> a sensible default candle interval for that range.
_INTERVAL_FOR_PERIOD = {
    "1d": "5m",
    "5d": "15m",
    "1mo": "1h",
    "3mo": "1d",
    "6mo": "1d",
    "1y": "1d",
    "2y": "1d",
    "5y": "1wk",
    "max": "1wk",
}

VALID_PERIODS = list(_INTERVAL_FOR_PERIOD.keys())


@dataclass
class StockSnapshot:
    """A lightweight, UI-friendly summary of a single ticker."""

    ticker: str
    name: str
    currency: str
    price: Optional[float]
    previous_close: Optional[float]
    change: Optional[float]
    change_pct: Optional[float]
    market_cap: Optional[float]
    volume: Optional[float]
    pe_ratio: Optional[float]
    week52_high: Optional[float]
    week52_low: Optional[float]
    sector: Optional[str]
    beta: Optional[float]


def _safe(info: dict, *keys):
    """Return the first present, non-null value among ``keys`` from ``info``."""
    for key in keys:
        value = info.get(key)
        if value is not None:
            return value
    return None


@_cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, period: str = "1y",
                  interval: Optional[str] = None) -> pd.DataFrame:
    """Return OHLCV history for ``ticker``.

    Parameters
    ----------
    ticker:
        Symbol such as ``"AAPL"``.
    period:
        One of :data:`VALID_PERIODS`.
    interval:
        Candle size. When ``None`` a sensible default is chosen for the period.

    Returns
    -------
    pandas.DataFrame
        Indexed by timezone-naive datetime with columns
        ``Open, High, Low, Close, Volume``. Empty on failure.
    """
    period = period if period in _INTERVAL_FOR_PERIOD else "1y"
    interval = interval or _INTERVAL_FOR_PERIOD[period]

    try:
        frame = yf.Ticker(ticker).history(period=period, interval=interval,
                                           auto_adjust=False)
    except Exception:
        return pd.DataFrame()

    if frame is None or frame.empty:
        return pd.DataFrame()

    frame = frame.rename(columns=str.title)
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in frame]
    frame = frame[keep].dropna(how="all")

    # Strip timezone for clean, comparable indices across tickers.
    if isinstance(frame.index, pd.DatetimeIndex) and frame.index.tz is not None:
        frame.index = frame.index.tz_localize(None)

    return frame


@_cache_data(ttl=300, show_spinner=False)
def fetch_snapshot(ticker: str) -> Optional[StockSnapshot]:
    """Return a :class:`StockSnapshot` for ``ticker`` or ``None`` on failure."""
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}

    price = _safe(info, "currentPrice", "regularMarketPrice", "previousClose")
    prev = _safe(info, "regularMarketPreviousClose", "previousClose")

    if price is None:
        # Fall back to the most recent close if .info is unavailable.
        hist = fetch_history(ticker, period="5d")
        if hist.empty:
            return None
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price

    change = (price - prev) if (price is not None and prev) else None
    change_pct = (change / prev * 100) if (change is not None and prev) else None

    return StockSnapshot(
        ticker=ticker.upper(),
        name=_safe(info, "longName", "shortName") or ticker.upper(),
        currency=_safe(info, "currency") or "USD",
        price=price,
        previous_close=prev,
        change=change,
        change_pct=change_pct,
        market_cap=_safe(info, "marketCap"),
        volume=_safe(info, "volume", "regularMarketVolume"),
        pe_ratio=_safe(info, "trailingPE", "forwardPE"),
        week52_high=_safe(info, "fiftyTwoWeekHigh"),
        week52_low=_safe(info, "fiftyTwoWeekLow"),
        sector=_safe(info, "sector"),
        beta=_safe(info, "beta"),
    )


@_cache_data(ttl=900, show_spinner=False)
def fetch_news(ticker: str, limit: int = 6) -> list[dict]:
    """Return a list of recent news items for ``ticker``.

    Each item is normalized to ``{title, publisher, link, published}`` so the
    UI does not depend on Yahoo's raw schema.
    """
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        return []

    items: list[dict] = []
    for entry in raw[:limit]:
        content = entry.get("content", entry)
        title = content.get("title") or entry.get("title")
        if not title:
            continue
        provider = content.get("provider", {})
        link = (content.get("canonicalUrl", {}) or {}).get("url") \
            or entry.get("link", "")
        ts = entry.get("providerPublishTime")
        published = (
            _dt.datetime.fromtimestamp(ts).strftime("%b %d, %Y %H:%M")
            if isinstance(ts, (int, float)) else content.get("pubDate", "")
        )
        items.append({
            "title": title,
            "publisher": provider.get("displayName") or entry.get("publisher", "—"),
            "link": link,
            "published": published,
        })
    return items


@_cache_data(ttl=600, show_spinner=False)
def fetch_many_closes(tickers: tuple[str, ...], period: str = "1y") -> pd.DataFrame:
    """Return a DataFrame of aligned closing prices, one column per ticker.

    Tickers that fail to download are silently dropped. The result is forward/back
    filled so correlation and covariance math has no gaps.
    """
    closes = {}
    for tkr in tickers:
        hist = fetch_history(tkr, period=period)
        if not hist.empty:
            closes[tkr] = hist["Close"]
    if not closes:
        return pd.DataFrame()
    frame = pd.DataFrame(closes).sort_index()
    return frame.ffill().bfill()
