"""Paquete para cargar, validar y analizar ventas."""

from .loader import DataLoadError, JsonSalesRepository, load
from .validator import ValidationError, validate_sales

__all__ = [
    "DataLoadError",
    "JsonSalesRepository",
    "ValidationError",
    "load",
    "validate_sales",
]
