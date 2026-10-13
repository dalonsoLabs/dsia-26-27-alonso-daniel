"""-> Interfaz de línea de comandos para el pipeline de ventas."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import metrics
from .loader import DataLoadError, load
from .validator import ValidationError, validate_sales


LOGGER = logging.getLogger(__name__)


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """> Lee los ficheros de entrada y salida indicados por la persona usuaria."""
    parser = argparse.ArgumentParser(description="Valida y limpia un fichero de ventas.")
    parser.add_argument("--input", required=True, type=Path, help="CSV o JSON de ventas")
    parser.add_argument("--output", required=True, type=Path, help="CSV de ventas válidas")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """> Ejecuta carga, validación, cálculo de métricas y exportación."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    arguments = parse_arguments(argv)

    try:
        invalid_path = arguments.output.with_name(arguments.output.stem + "_invalidas.csv")
        for destination in (arguments.output, invalid_path):
            if destination.resolve() == arguments.input.resolve() or (
                destination.exists() and arguments.input.exists()
                and destination.samefile(arguments.input)
            ):
                raise ValidationError("Una salida sobrescribiría el fichero de entrada.")
        sales = load(arguments.input)
        valid_sales, invalid_sales = validate_sales(sales)
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        valid_sales.to_csv(arguments.output, index=False)
        invalid_sales.to_csv(invalid_path, index=False)
    except (DataLoadError, ValidationError, OSError) as error:
        LOGGER.error("No se pudo procesar la entrada: %s", error)
        raise SystemExit(1) from error

    LOGGER.info("Ventas válidas: %s | inválidas: %s", len(valid_sales), len(invalid_sales))
    LOGGER.info("Ventas limpias escritas en: %s", arguments.output)
    LOGGER.info("Importe por región:\n%s", metrics.total_by_region(valid_sales).to_string(index=False))
    LOGGER.info("Top productos:\n%s", metrics.top_products(valid_sales).to_string(index=False))
    LOGGER.info(
        "Clientes con más de una compra:\n%s",
        metrics.customers_with_multiple_purchases(valid_sales).to_string(index=False),
    )


if __name__ == "__main__":
    main()
