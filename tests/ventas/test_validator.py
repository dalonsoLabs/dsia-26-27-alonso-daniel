"""Validación, bordes y checkpoint del CSV del curso."""

from pathlib import Path

import pandas as pd
import pytest

from ventas_app.loader import load
from ventas_app.validator import ValidationError, validate_sales


def test_valid_invalid_amount_and_no_mutation(sales_frame):
    original = sales_frame.copy(deep=True)
    valid, invalid = validate_sales(sales_frame)
    assert len(valid) == 2
    assert len(invalid) == 1
    assert valid["importe"].tolist() == [20.0, 30.0]
    assert "unidades" in invalid.iloc[0]["motivo"]
    pd.testing.assert_frame_equal(sales_frame, original)


@pytest.mark.parametrize("column", ["unidades", "precio_unitario"])
@pytest.mark.parametrize("value, expected", [(0, 0), (-1, 0), (None, 0), ("mal", 0), (1, 1)])
def test_numeric_boundaries(sales_frame, column, value, expected):
    frame = sales_frame.iloc[:1].copy().astype({column: "object"})
    frame.loc[0, column] = value
    valid, invalid = validate_sales(frame)
    assert len(valid) == expected
    assert len(invalid) == 1 - expected


def test_missing_columns(sales_frame):
    with pytest.raises(ValidationError, match="cliente_id"):
        validate_sales(sales_frame.drop(columns="cliente_id"))


def test_empty_input_with_schema(sales_frame):
    valid, invalid = validate_sales(sales_frame.iloc[:0])
    assert valid.empty and invalid.empty
    assert "importe" in valid and "motivo" in invalid


@pytest.mark.integration
def test_course_csv_has_140_valid_and_10_invalid():
    source = Path(__file__).resolve().parents[2] / "E1_pandas" / "Datos" / "ventas.csv"
    valid, invalid = validate_sales(load(source))
    assert len(valid) == 140
    assert len(invalid) == 10
