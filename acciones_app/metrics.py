"""Métricas descriptivas por símbolo sobre barras diarias ya validadas."""

from __future__ import annotations

from math import sqrt

import pandas as pd


SESSIONS_PER_YEAR = 252


def price_return_by_symbol(bars: pd.DataFrame) -> pd.DataFrame:
    """Rentabilidad porcentual del cierre entre primera y última barra disponible.

    Con el dataset split-adjusted es rentabilidad del precio ajustado por splits;
    no incluye dividendos ni comisiones y no constituye total return.
    """
    ordered = bars.sort_values(["symbol", "timestamp"])
    result = ordered.groupby("symbol").agg(
        start=("timestamp", "first"), end=("timestamp", "last"),
        first_close=("close", "first"), last_close=("close", "last"),
        observations=("close", "size"),
    ).reset_index()
    result["return_pct"] = (result["last_close"] / result["first_close"] - 1) * 100
    return result


def average_volume_by_symbol(bars: pd.DataFrame) -> pd.DataFrame:
    """Media de acciones negociadas por barra diaria, sin rellenar sesiones ausentes."""
    return bars.groupby("symbol", as_index=False).agg(average_daily_volume=("volume", "mean"))


def volatility_by_symbol(bars: pd.DataFrame) -> pd.DataFrame:
    """Desviación muestral de retornos simples, anualizada con sqrt(252), en %.

    Se necesitan tres cierres para dos retornos. Si faltan sesiones, el retorno
    atraviesa ese hueco; la anualización supone observaciones diarias regulares.
    """
    ordered = bars.sort_values(["symbol", "timestamp"]).copy()
    ordered["return"] = ordered.groupby("symbol")["close"].pct_change(fill_method=None)
    result = ordered.groupby("symbol", as_index=False).agg(
        return_observations=("return", "count"), daily_std=("return", "std")
    )
    result["annualized_volatility_pct"] = result.pop("daily_std") * sqrt(SESSIONS_PER_YEAR) * 100
    return result
