"""Agregaciones conocidas sobre una fixture, siguiendo Arrange/Act/Assert."""

from ventas_app import metrics
from ventas_app.validator import validate_sales


def test_known_region_total(sales_frame):
    # Arrange: dos compras de Norte por 20 y 30.
    valid, _ = validate_sales(sales_frame)
    # Act
    result = metrics.total_by_region(valid)
    # Assert
    assert result.to_dict("records") == [{"region": "Norte", "importe": 50.0}]


def test_products_and_limit(sales_frame):
    valid, _ = validate_sales(sales_frame)
    assert metrics.top_products(valid, limit=1).to_dict("records") == [{"producto": "A", "importe": 50.0}]
    assert metrics.top_products(valid, limit=0).empty


def test_repeat_customers(sales_frame):
    valid, _ = validate_sales(sales_frame)
    assert metrics.customers_with_multiple_purchases(valid).to_dict("records") == [{"cliente_id": "C1", "compras": 2}]


def test_empty_metrics(sales_frame):
    valid, _ = validate_sales(sales_frame.iloc[:0])
    assert metrics.total_by_region(valid).empty
    assert metrics.top_products(valid).empty
    assert metrics.customers_with_multiple_purchases(valid).empty
