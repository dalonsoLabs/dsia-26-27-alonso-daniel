""">> Carga de ventas y traducción de errores a excepciones de dominio."""

import pandas as pd
import pytest

from ventas_app.loader import DataLoadError, load, load_from


@pytest.mark.parametrize("extension", ["csv", "json"])
def test_load_sales(tmp_path, sales_frame, extension):
    path = tmp_path / f"ventas.{extension}"
    if extension == "csv":
        sales_frame.to_csv(path, index=False)
    else:
        sales_frame.to_json(path, orient="records")
    result = load(path)
    pd.testing.assert_frame_equal(result, sales_frame, check_dtype=False)


@pytest.mark.parametrize("extension", ["csv", "json"])
def test_missing_source_raises_domain_error(tmp_path, extension):
    with pytest.raises(DataLoadError, match="No existe"):
        load(tmp_path / f"missing.{extension}")


@pytest.mark.parametrize("content", ["{", "{}", "[1, 2]"])
def test_invalid_json_is_domain_error(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataLoadError):
        load(path)


def test_empty_csv_is_domain_error(tmp_path):
    path = tmp_path / "empty.csv"
    path.touch()
    with pytest.raises(DataLoadError):
        load(path)


@pytest.mark.parametrize("extension", ["csv", "json"])
def test_invalid_encoding_is_domain_error(tmp_path, extension):
    path = tmp_path / f"bad.{extension}"
    path.write_bytes(b"\xff")
    with pytest.raises(DataLoadError):
        load(path)


def test_unsupported_format(tmp_path):
    with pytest.raises(DataLoadError, match="Formato no soportado"):
        load(tmp_path / "ventas.xlsx")


def test_repository_contract(sales_frame):
    class MemorySalesRepository:
        def load(self):
            return sales_frame.copy()
    pd.testing.assert_frame_equal(load_from(MemorySalesRepository()), sales_frame)
