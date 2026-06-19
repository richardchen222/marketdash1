"""Utility layer for the stock analytics dashboard.

Exposes data access, technical indicators, portfolio analytics and AI-style
insight generation so the UI layer can stay thin and declarative.

The pure-math modules (:mod:`indicators`, :mod:`analytics`, :mod:`insights`)
import with only pandas/numpy installed. Modules that need optional runtime
dependencies (``yfinance`` for :mod:`data_loader`/:mod:`market`) are imported
defensively so the math layer stays importable and unit-testable in isolation.
"""

from . import indicators, analytics, insights  # noqa: F401

__all__ = ["indicators", "analytics", "insights"]

try:  # Optional: requires yfinance at runtime.
    from . import data_loader, market  # noqa: F401

    __all__ += ["data_loader", "market"]
except ModuleNotFoundError:  # pragma: no cover
    pass
