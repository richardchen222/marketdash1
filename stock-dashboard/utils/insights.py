"""Rule-based "AI Insights" engine.

Generates plain-English observations from the enriched price frame: trend
classification, anomaly detection on daily returns, momentum read from RSI/MACD
and a simple sentiment summary. Deliberately deterministic and dependency-free
so the portfolio piece runs offline with no API keys, while the output reads
like an analyst's quick take.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import analytics, indicators


@dataclass
class Insight:
    """A single generated observation."""

    icon: str          # emoji used as a lightweight visual marker
    title: str
    detail: str
    tone: str          # "positive" | "negative" | "neutral"


def _anomalies(close: pd.Series, z_threshold: float = 2.5) -> list[Insight]:
    """Flag days whose return is a statistical outlier (|z| > threshold)."""
    rets = analytics.daily_returns(close)
    if rets.empty or rets.std() == 0:
        return []

    z = (rets - rets.mean()) / rets.std()
    outliers = z[z.abs() > z_threshold]
    insights: list[Insight] = []

    for date, score in outliers.tail(3).items():
        move = rets.loc[date] * 100
        direction = "surge" if move > 0 else "drop"
        tone = "positive" if move > 0 else "negative"
        insights.append(Insight(
            icon="⚡",
            title=f"Unusual {direction} on {pd.Timestamp(date):%b %d}",
            detail=(f"Price moved {move:+.2f}% that day — roughly "
                    f"{abs(score):.1f} standard deviations from normal, "
                    "a statistically unusual move."),
            tone=tone,
        ))
    return insights


def _momentum(frame: pd.DataFrame) -> list[Insight]:
    """Read RSI and MACD for a momentum/overbought-oversold call."""
    insights: list[Insight] = []
    if "RSI" not in frame or frame["RSI"].dropna().empty:
        return insights

    rsi_now = float(frame["RSI"].iloc[-1])
    if rsi_now >= 70:
        insights.append(Insight("🔥", "Overbought signal",
                                f"RSI sits at {rsi_now:.0f}. Readings above 70 "
                                "often precede a cooling-off period.", "negative"))
    elif rsi_now <= 30:
        insights.append(Insight("🧊", "Oversold signal",
                                f"RSI sits at {rsi_now:.0f}. Readings below 30 "
                                "can mark a potential rebound zone.", "positive"))
    else:
        insights.append(Insight("⚖️", "Neutral momentum",
                                f"RSI is balanced at {rsi_now:.0f}, suggesting "
                                "neither overbought nor oversold conditions.",
                                "neutral"))

    if {"MACD", "MACD_SIGNAL"}.issubset(frame.columns):
        macd_now = frame["MACD"].iloc[-1]
        sig_now = frame["MACD_SIGNAL"].iloc[-1]
        if macd_now > sig_now:
            insights.append(Insight("📈", "Bullish MACD",
                                    "MACD is above its signal line — short-term "
                                    "momentum is tilting upward.", "positive"))
        else:
            insights.append(Insight("📉", "Bearish MACD",
                                    "MACD is below its signal line — short-term "
                                    "momentum is tilting downward.", "negative"))
    return insights


def _trend(frame: pd.DataFrame) -> list[Insight]:
    """Summarize the moving-average trend structure."""
    label = indicators.trend_label(frame)
    tone = ("positive" if "Up" in label
            else "negative" if "Down" in label else "neutral")
    return [Insight("🧭", f"Trend: {label}",
                    "Based on the alignment of the 20-, 50- and 200-day moving "
                    "averages.", tone)]


def _performance(close: pd.Series) -> list[Insight]:
    """Headline performance and volatility read over the window."""
    if close.empty:
        return []
    total = (close.iloc[-1] / close.iloc[0] - 1) * 100
    vol = analytics.annualized_volatility(close)
    tone = "positive" if total >= 0 else "negative"
    return [Insight(
        "📊", f"Window return {total:+.1f}%",
        f"Annualized volatility is {vol:.1f}%, "
        f"{'elevated' if vol > 35 else 'moderate' if vol > 20 else 'subdued'} "
        "relative to the broad market.", tone,
    )]


def generate(frame: pd.DataFrame) -> list[Insight]:
    """Produce the full ordered list of insights for an enriched frame."""
    if frame.empty:
        return [Insight("ℹ️", "No data", "No price history is available to "
                        "analyze for this symbol.", "neutral")]

    close = frame["Close"]
    insights: list[Insight] = []
    insights += _trend(frame)
    insights += _performance(close)
    insights += _momentum(frame)
    insights += _anomalies(close)
    return insights


def sentiment_score(frame: pd.DataFrame) -> tuple[int, str]:
    """Blend signals into a 0–100 sentiment score and a label.

    Combines window return, RSI position and MACD posture. Purely heuristic and
    intended as a visual summary, not financial advice.
    """
    if frame.empty:
        return 50, "Neutral"

    close = frame["Close"]
    score = 50.0

    total = (close.iloc[-1] / close.iloc[0] - 1)
    score += np.clip(total * 100, -20, 20)

    if "RSI" in frame and not frame["RSI"].dropna().empty:
        rsi_now = frame["RSI"].iloc[-1]
        score += np.clip((rsi_now - 50) * 0.4, -15, 15)

    if {"MACD", "MACD_SIGNAL"}.issubset(frame.columns):
        score += 10 if frame["MACD"].iloc[-1] > frame["MACD_SIGNAL"].iloc[-1] else -10

    score = int(np.clip(score, 0, 100))
    label = ("Extreme Greed" if score >= 80 else "Greed" if score >= 60
             else "Neutral" if score >= 40 else "Fear" if score >= 20
             else "Extreme Fear")
    return score, label
