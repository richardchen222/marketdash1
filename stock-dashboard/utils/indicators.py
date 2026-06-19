"""Technical indicator calculations.

Pure functions over pandas Series/DataFrames — no I/O, no Streamlit. This makes
the math easy to reason about and trivial to unit test. Every function returns
new objects and never mutates its inputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def moving_average(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average over ``window`` periods."""
    return series.rolling(window=window, min_periods=1).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing).

    Returns values in the 0–100 range. Values above 70 conventionally signal
    overbought conditions and below 30 oversold.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26,
         signal: int = 9) -> pd.DataFrame:
    """Moving Average Convergence Divergence.

    Returns a DataFrame with ``macd``, ``signal`` and ``hist`` columns.
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "hist": macd_line - signal_line,
    })


def bollinger_bands(series: pd.Series, window: int = 20,
                    num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands with ``upper``, ``middle`` and ``lower`` columns."""
    middle = series.rolling(window=window, min_periods=1).mean()
    std = series.rolling(window=window, min_periods=1).std(ddof=0)
    return pd.DataFrame({
        "upper": middle + num_std * std,
        "middle": middle,
        "lower": middle - num_std * std,
    })


def enrich(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach the full indicator suite to an OHLCV frame.

    Adds moving averages, RSI, MACD trio and Bollinger Bands as new columns.
    Returns a copy so the source frame is untouched.
    """
    if frame.empty:
        return frame

    out = frame.copy()
    close = out["Close"]

    out["MA20"] = moving_average(close, 20)
    out["MA50"] = moving_average(close, 50)
    out["MA200"] = moving_average(close, 200)
    out["RSI"] = rsi(close)

    macd_df = macd(close)
    out["MACD"] = macd_df["macd"]
    out["MACD_SIGNAL"] = macd_df["signal"]
    out["MACD_HIST"] = macd_df["hist"]

    bb = bollinger_bands(close)
    out["BB_UPPER"] = bb["upper"]
    out["BB_MIDDLE"] = bb["middle"]
    out["BB_LOWER"] = bb["lower"]

    return out


def signal_crossovers(frame: pd.DataFrame) -> pd.DataFrame:
    """Detect golden/death crossovers between the 20- and 50-day averages.

    Returns a frame with ``date``, ``price`` and ``type`` (``buy``/``sell``)
    columns — one row per crossover event, suitable for chart annotation.
    """
    if frame.empty or "MA20" not in frame or "MA50" not in frame:
        return pd.DataFrame(columns=["date", "price", "type"])

    spread = frame["MA20"] - frame["MA50"]
    sign = np.sign(spread)
    flips = sign.diff().fillna(0)

    events = []
    for idx, flip in flips.items():
        if flip > 0:
            events.append({"date": idx, "price": frame.loc[idx, "Close"],
                           "type": "buy"})
        elif flip < 0:
            events.append({"date": idx, "price": frame.loc[idx, "Close"],
                           "type": "sell"})
    return pd.DataFrame(events)


def trend_label(frame: pd.DataFrame) -> str:
    """Classify the current trend from MA alignment as a short human label."""
    if frame.empty or frame[["MA20", "MA50", "MA200"]].iloc[-1].isna().any():
        return "Insufficient data"

    last = frame.iloc[-1]
    if last["MA20"] > last["MA50"] > last["MA200"]:
        return "Strong Uptrend"
    if last["MA20"] > last["MA50"]:
        return "Uptrend"
    if last["MA20"] < last["MA50"] < last["MA200"]:
        return "Strong Downtrend"
    if last["MA20"] < last["MA50"]:
        return "Downtrend"
    return "Sideways / Consolidating"
