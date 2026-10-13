"""Repositorios para CSV y JSONL de barras descargadas de Alpaca."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Protocol

import pandas as pd


API_FIELDS = {"t": "timestamp", "o": "open", "h": "high", "l": "low",
              "c": "close", "v": "volume", "n": "trade_count", "vw": "vwap"}


class DataLoadError(Exception):
    """La fuente de barras no existe o no se puede interpretar."""


class BarsRepository(Protocol):
    """Contrato de una fuente de barras independiente de su formato."""

    def load(self) -> pd.DataFrame:
        """Devuelve las barras sin validar sus valores de negocio."""


class CsvBarsRepository:
    """Lee el CSV tabular producido por descargar_alpaca.py."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> pd.DataFrame:
        """Carga el CSV o traduce el error de lectura a una excepción de dominio."""
        try:
            return pd.read_csv(self._path)
        except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise DataLoadError(f"No se pudo leer el CSV: {self._path}") from error


class JsonlBarsRepository:
    """Lee un lote JSONL de Alpaca, opcionalmente comprimido con gzip."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> pd.DataFrame:
        """Normaliza los nombres de campos compactos de la API al esquema CSV."""
        opener = gzip.open if self._path.suffix.lower() == ".gz" else open
        records = []
        try:
            with opener(self._path, "rt", encoding="utf-8") as source:
                for number, line in enumerate(source, 1):
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise DataLoadError(f"La línea {number} debe ser un objeto JSON.")
                    normalized = {API_FIELDS.get(key, key): value for key, value in record.items()}
                    if len(normalized) != len(record):
                        raise DataLoadError(f"Campos ambiguos en la línea {number}.")
                    records.append(normalized)
        except (OSError, EOFError, UnicodeError, json.JSONDecodeError) as error:
            raise DataLoadError(f"No se pudo leer el JSONL: {self._path}") from error
        return pd.DataFrame.from_records(records)


def load(path: str | Path) -> pd.DataFrame:
    """Selecciona el repositorio por extensión; admite CSV, JSONL y JSONL.GZ."""
    source = Path(path)
    if source.suffix.lower() == ".csv":
        repository: BarsRepository = CsvBarsRepository(source)
    elif source.name.lower().endswith((".jsonl", ".jsonl.gz")):
        repository = JsonlBarsRepository(source)
    else:
        raise DataLoadError("Formato no soportado. Usa CSV, JSONL o JSONL.GZ.")
    return repository.load()
