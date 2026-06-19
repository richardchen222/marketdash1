"""Unit tests for the pure-function layers (no network required).

Run with: ``pytest`` from the project root. These cover the math in
:mod:`utils.indicators`, :mod:`utils.analytics` and :mod:`utils.insights`
so the resume project demonstrates a real testing habit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from utils import analytics, indicators, insights


@pytest.fixture
def trending_frame() -> pd.DataFrame:
    """A synthetic uptrending OHLCV frame for deterministic tests."""
    idx = pd.date_range("2023-01-01", periods=260, freq="D")
    close = pd.Series(np.linspace(100, 200, 260), index=idx) \
        + np.sin(np.linspace(0, 20, 260)) * 3
    frame = pd.DataFrame({
        "Open": close.shift(1).fillna(close.iloc[0]),
        "High": close + 1.5,
        "Low": close - 1.5,
        "Close": close,
        "Volume": pd.Series(np.random.randint(1e6, 5e6, 260), index=idx),
    })
    return frame


def test_rsi_bounds(trending_frame):
    r = indicators.rsi(trending_frame["Close"])
    assert r.between(0, 100).all()


def test_enrich_adds_columns(trending_frame):
    out = indicators.enrich(trending_frame)
    for col in ["MA20", "MA50", "MA200", "RSI", "MACD", "BB_UPPER"]:
        assert col in out.columns


def test_trend_label_uptrend(trending_frame):
    out = indicators.enrich(trending_frame)
    assert "Uptrend" in indicators.trend_label(out)


def test_sharpe_finite(trending_frame):
    s = analytics.sharpe_ratio(trending_frame["Close"])
    assert np.isfinite(s)


def test_max_drawdown_non_positive(trending_frame):
    assert analytics.max_drawdown(trending_frame["Close"]) <= 0


def test_beta_self_is_one(trending_frame):
    close = trending_frame["Close"]
    assert analytics.beta(close, close) == pytest.approx(1.0, abs=1e-6)


def test_sentiment_in_range(trending_frame):
    out = indicators.enrich(trending_frame)
    score, label = insights.sentiment_score(out)
    assert 0 <= score <= 100
    assert isinstance(label, str)


def test_empty_inputs_are_safe():
    empty = pd.Series(dtype=float)
    assert analytics.annualized_volatility(empty) == 0.0
    assert analytics.sharpe_ratio(empty) == 0.0
    assert indicators.enrich(pd.DataFrame()).empty
