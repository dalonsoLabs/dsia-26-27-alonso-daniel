"""Repositorios y funciones de carga para las fuentes de ventas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import pandas as pd


class DataLoadError(Exception):
    """Se lanza cuando no se puede leer el fichero de datos."""


class SalesRepository(Protocol):
    """Contrato que debe cumplir cualquier origen de ventas."""

    def load(self) -> pd.DataFrame:
        """Devuelve las ventas como un DataFrame."""


class CsvSalesRepository:
    """Repositorio de ventas almacenadas en un fichero CSV."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> pd.DataFrame:
        if not self._path.is_file():
            raise DataLoadError(f"No existe el fichero: {self._path}")

        try:
            return pd.read_csv(self._path)
        except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise DataLoadError(f"No se pudo leer el CSV: {self._path}") from error


class JsonSalesRepository:
    """Repositorio de ventas en JSON con una lista de registros."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> pd.DataFrame:
        if not self._path.is_file():
            raise DataLoadError(f"No existe el fichero: {self._path}")

        try:
            with self._path.open(encoding="utf-8") as sales_file:
                records = json.load(sales_file)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise DataLoadError(f"No se pudo leer el JSON: {self._path}") from error

        if not isinstance(records, list):
            raise DataLoadError("El JSON debe contener una lista de registros de ventas.")
        if not all(isinstance(record, dict) for record in records):
            raise DataLoadError("Cada registro de ventas debe ser un objeto JSON.")

        return pd.DataFrame.from_records(records)


def load(path: str | Path) -> pd.DataFrame:
    """Carga ventas desde un CSV o un JSON según la extensión del fichero."""
    source_path = Path(path)
    repositories: dict[str, type[CsvSalesRepository] | type[JsonSalesRepository]] = {
        ".csv": CsvSalesRepository,
        ".json": JsonSalesRepository,
    }
    repository_class = repositories.get(source_path.suffix.lower())

    if repository_class is None:
        raise DataLoadError("Formato no soportado. Usa un fichero .csv o .json.")

    repository: SalesRepository = repository_class(source_path)
    return load_from(repository)


def load_from(repository: SalesRepository) -> pd.DataFrame:
    """Carga ventas desde cualquier repositorio que cumpla el contrato."""
    return repository.load()
