"""-> CLI de carga, validación, métricas y exportación de acciones."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import metrics
from .loader import DataLoadError, load
from .validator import ValidationError, validate_bars


LOGGER = logging.getLogger(__name__)


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """> Lee las rutas de entrada y del CSV válido a exportar."""
    parser = argparse.ArgumentParser(description="Valida y analiza barras diarias de acciones.")
    parser.add_argument("--input", required=True, type=Path, help="CSV, JSONL o JSONL.GZ de barras")
    parser.add_argument("--output", required=True, type=Path, help="CSV de barras válidas")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """> Ejecuta el pipeline y escribe barras, rechazos y tres métricas en CSV."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_arguments(argv)
    try:
        valid, invalid = validate_bars(load(args.input))
        reports = {
            "invalidas": invalid,
            "rentabilidad": metrics.price_return_by_symbol(valid),
            "volumen": metrics.average_volume_by_symbol(valid),
            "volatilidad": metrics.volatility_by_symbol(valid),
        }
        destinations = [args.output, *(
            args.output.with_name(f"{args.output.stem}_{name}.csv") for name in reports
        )]
        for destination in destinations:
            if destination.resolve() == args.input.resolve() or (
                destination.exists() and args.input.exists() and destination.samefile(args.input)
            ):
                raise ValidationError("Una salida sobrescribiría el fichero de entrada.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        valid.to_csv(args.output, index=False)
        for name, report in reports.items():
            path = args.output.with_name(f"{args.output.stem}_{name}.csv")
            report.to_csv(path, index=False)
    except (DataLoadError, ValidationError, OSError) as error:
        LOGGER.error("No se pudo procesar la entrada: %s", error)
        raise SystemExit(1) from error
    LOGGER.info("Barras válidas: %s | inválidas: %s", len(valid), len(invalid))
    for name in ("rentabilidad", "volumen", "volatilidad"):
        LOGGER.info("%s:\n%s", name, reports[name].to_string(index=False))


if __name__ == "__main__":
    main()
