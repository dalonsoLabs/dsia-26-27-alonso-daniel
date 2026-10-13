"""Reglas de validación de ventas."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {"region", "producto", "unidades", "precio_unitario", "cliente_id"}
MINIMUM_POSITIVE_VALUE = 0


class ValidationError(Exception):
    """Se lanza cuando la estructura de las ventas no permite validarlas."""


def validate_sales(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa ventas válidas e inválidas y calcula el importe de las válidas."""
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_names = ", ".join(sorted(missing_columns))
        raise ValidationError(f"Faltan columnas obligatorias: {missing_names}")

    sales = frame.copy()
    sales["unidades"] = pd.to_numeric(sales["unidades"], errors="coerce")
    sales["precio_unitario"] = pd.to_numeric(sales["precio_unitario"], errors="coerce")

    valid_units = sales["unidades"].gt(MINIMUM_POSITIVE_VALUE)
    valid_prices = sales["precio_unitario"].gt(MINIMUM_POSITIVE_VALUE)
    valid_mask = valid_units & valid_prices

    valid_sales = sales.loc[valid_mask].copy()
    valid_sales["importe"] = (
        valid_sales["unidades"] * valid_sales["precio_unitario"]
    )

    invalid_sales = sales.loc[~valid_mask].copy()
    invalid_sales["motivo"] = _invalid_reasons(invalid_sales)
    return valid_sales.reset_index(drop=True), invalid_sales.reset_index(drop=True)


def _invalid_reasons(invalid_sales: pd.DataFrame) -> pd.Series:
    """Describe qué regla incumple cada fila inválida."""
    reasons: list[str] = []
    for row in invalid_sales.itertuples(index=False):
        row_reasons: list[str] = []
        if pd.isna(row.unidades) or row.unidades <= MINIMUM_POSITIVE_VALUE:
            row_reasons.append("unidades inválidas")
        if pd.isna(row.precio_unitario) or row.precio_unitario <= MINIMUM_POSITIVE_VALUE:
            row_reasons.append("precio_unitario inválido")
        reasons.append("; ".join(row_reasons))
    return pd.Series(reasons, index=invalid_sales.index, dtype="object")
