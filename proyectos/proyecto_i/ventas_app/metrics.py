"""-> Agregaciones calculadas únicamente a partir de ventas ya válidas."""

from __future__ import annotations

import pandas as pd


TOP_PRODUCTS_LIMIT = 3
MINIMUM_REPEAT_PURCHASES = 1


def total_by_region(valid_sales: pd.DataFrame) -> pd.DataFrame:
    """> Calcula el importe total por región, de mayor a menor."""
    return _total_by_column(valid_sales, "region")


def top_products(
    valid_sales: pd.DataFrame, limit: int = TOP_PRODUCTS_LIMIT
) -> pd.DataFrame:
    """> Devuelve los productos con mayor importe acumulado."""
    return _total_by_column(valid_sales, "producto").head(limit)


def customers_with_multiple_purchases(valid_sales: pd.DataFrame) -> pd.DataFrame:
    """> Lista clientes que aparecen en más de una venta válida."""
    purchases = valid_sales["cliente_id"].value_counts()
    repeated_customers = purchases[purchases > MINIMUM_REPEAT_PURCHASES]
    return repeated_customers.rename_axis("cliente_id").reset_index(name="compras")


def _total_by_column(valid_sales: pd.DataFrame, column: str) -> pd.DataFrame:
    """> Agrupa el importe por una columna y lo ordena descendentemente."""
    return (
        valid_sales.groupby(column, as_index=False)["importe"]
        .sum()
        .sort_values("importe", ascending=False, ignore_index=True)
    )
