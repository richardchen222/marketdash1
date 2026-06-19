"""Portfolio and risk analytics.

Quant building blocks (returns, Sharpe, beta, drawdown, volatility) implemented
as pure functions. Trading-day annualization uses 252 periods. All functions
guard against empty or degenerate inputs and return ``float`` / DataFrame types
the UI can render without further checks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def daily_returns(close: pd.Series) -> pd.Series:
    """Simple daily percentage returns."""
    return close.pct_change().dropna()


def cumulative_returns(close: pd.Series) -> pd.Series:
    """Cumulative growth of $1 invested at the start of the window."""
    rets = daily_returns(close)
    return (1 + rets).cumprod() - 1


def annualized_volatility(close: pd.Series) -> float:
    """Annualized standard deviation of daily returns (as a percentage)."""
    rets = daily_returns(close)
    if rets.empty:
        return 0.0
    return float(rets.std() * np.sqrt(TRADING_DAYS) * 100)


def sharpe_ratio(close: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Annualized Sharpe ratio.

    ``risk_free_rate`` is an annual rate (e.g. ``0.04`` for 4%). Returns 0 when
    volatility is zero to avoid division blow-ups.
    """
    rets = daily_returns(close)
    if rets.empty or rets.std() == 0:
        return 0.0
    excess = rets.mean() - (risk_free_rate / TRADING_DAYS)
    return float((excess / rets.std()) * np.sqrt(TRADING_DAYS))


def max_drawdown(close: pd.Series) -> float:
    """Maximum peak-to-trough decline over the window (as a percentage)."""
    if close.empty:
        return 0.0
    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    return float(drawdown.min() * 100)


def beta(asset_close: pd.Series, benchmark_close: pd.Series) -> float:
    """Beta of an asset against a benchmark via covariance / variance."""
    asset = daily_returns(asset_close)
    bench = daily_returns(benchmark_close)
    joined = pd.concat([asset, bench], axis=1, join="inner").dropna()
    if joined.shape[0] < 2 or joined.iloc[:, 1].var() == 0:
        return 0.0
    cov = np.cov(joined.iloc[:, 0], joined.iloc[:, 1])[0][1]
    return float(cov / joined.iloc[:, 1].var())


def rolling_volatility(close: pd.Series, window: int = 21) -> pd.Series:
    """Rolling annualized volatility (percentage), default ~1 month window."""
    rets = daily_returns(close)
    return rets.rolling(window=window).std() * np.sqrt(TRADING_DAYS) * 100


def correlation_matrix(closes: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix of daily returns across multiple tickers."""
    if closes.empty:
        return pd.DataFrame()
    return closes.pct_change().dropna().corr()


def portfolio_summary(holdings: pd.DataFrame,
                      price_map: dict[str, float]) -> dict:
    """Aggregate a holdings table into portfolio-level metrics.

    Parameters
    ----------
    holdings:
        Columns ``ticker``, ``shares``, ``cost_basis`` (per-share purchase price).
    price_map:
        Current price per ticker.

    Returns
    -------
    dict
        ``total_value``, ``total_cost``, ``total_pl``, ``total_pl_pct`` plus an
        ``allocation`` DataFrame (ticker, value, weight) for the donut chart.
    """
    rows = []
    for _, row in holdings.iterrows():
        tkr = str(row["ticker"]).upper()
        shares = float(row["shares"])
        cost = float(row["cost_basis"])
        price = float(price_map.get(tkr, cost))
        value = shares * price
        rows.append({
            "ticker": tkr,
            "shares": shares,
            "price": price,
            "value": value,
            "cost": shares * cost,
        })

    table = pd.DataFrame(rows)
    if table.empty:
        return {"total_value": 0.0, "total_cost": 0.0, "total_pl": 0.0,
                "total_pl_pct": 0.0, "allocation": pd.DataFrame()}

    total_value = table["value"].sum()
    total_cost = table["cost"].sum()
    total_pl = total_value - total_cost
    total_pl_pct = (total_pl / total_cost * 100) if total_cost else 0.0

    allocation = table[["ticker", "value"]].copy()
    allocation["weight"] = allocation["value"] / total_value * 100

    return {
        "total_value": float(total_value),
        "total_cost": float(total_cost),
        "total_pl": float(total_pl),
        "total_pl_pct": float(total_pl_pct),
        "allocation": allocation,
    }
