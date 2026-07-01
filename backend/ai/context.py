"""Cached analytics data shared by tools and recommendation chain."""

from __future__ import annotations

from contextvars import ContextVar

import pandas as pd

from analytics.market_basket import market_basket
from analytics.menu_engineering import menu_engineering
from db import load_transaction_data


class AnalyticsContext:
    """
    Holds transaction data and exposes Phase 2 results lazily.

    Two ways to build one:
      - default (no args): loads the demo dataset from Postgres on first use.
      - preloaded frames: pass items_df/lines_df from an uploaded dataset.

    Both the dashboard pipeline and agent tools read from the same cached
    DataFrames so metrics never diverge between code paths.
    """

    def __init__(
        self,
        items_df: pd.DataFrame | None = None,
        orders_df: pd.DataFrame | None = None,
        lines_df: pd.DataFrame | None = None,
    ) -> None:
        self._items_df = items_df
        self._orders_df = orders_df
        self._lines_df = lines_df
        self._matrix_df: pd.DataFrame | None = None
        self._associations_df: pd.DataFrame | None = None
        # Preloaded contexts must never fall back to the Postgres demo data.
        self._preloaded = items_df is not None and lines_df is not None

    def refresh(self) -> None:
        """Reload all data from Postgres (only valid for the default context)."""
        if self._preloaded:
            return
        self._items_df = None
        self._orders_df = None
        self._lines_df = None
        self._matrix_df = None
        self._associations_df = None
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        if self._items_df is None and not self._preloaded:
            self._items_df, self._orders_df, self._lines_df = load_transaction_data()
        if self._matrix_df is None:
            self._matrix_df = menu_engineering(self._items_df, self._lines_df)
        if self._associations_df is None:
            self._associations_df = market_basket(
                self._lines_df, items_df=self._items_df
            )

    @property
    def items_df(self) -> pd.DataFrame:
        self._ensure_loaded()
        assert self._items_df is not None
        return self._items_df

    @property
    def lines_df(self) -> pd.DataFrame:
        self._ensure_loaded()
        assert self._lines_df is not None
        return self._lines_df

    @property
    def matrix_df(self) -> pd.DataFrame:
        self._ensure_loaded()
        assert self._matrix_df is not None
        return self._matrix_df

    @property
    def associations_df(self) -> pd.DataFrame:
        self._ensure_loaded()
        assert self._associations_df is not None
        return self._associations_df


# Module-level singleton for the default demo dataset.
analytics_context = AnalyticsContext()

# Per-request "active" context. The chat agent's tools are decoupled from the
# request, so we expose the right dataset (default or uploaded) via a ContextVar
# that the endpoint sets before invoking the agent.
_active_context: ContextVar[AnalyticsContext | None] = ContextVar(
    "active_analytics_context", default=None
)


def get_active_context() -> AnalyticsContext:
    """Return the context bound to the current request, or the default dataset."""
    return _active_context.get() or analytics_context


def set_active_context(ctx: AnalyticsContext):
    """Bind a context for the current request; returns a reset token."""
    return _active_context.set(ctx)


def reset_active_context(token) -> None:
    """Restore the previous active context using the token from set_active_context."""
    _active_context.reset(token)
