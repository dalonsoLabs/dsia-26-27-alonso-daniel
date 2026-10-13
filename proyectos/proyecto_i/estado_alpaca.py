"""-> Muestra el avance de las descargas de Alpaca a partir de archivos terminados."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

from descargar_alpaca_eventos import periods
from descargar_alpaca_masivo import stocks


RAW = Path(__file__).parent / "data" / "raw"
ROOT = RAW / "masivo"
END = date(2026, 9, 28)


def summary(name: str, expected: int) -> None:
    directory = ROOT / name
    manifests = list(directory.glob("*.manifest.json"))
    rows = sum(json.loads(path.read_text(encoding="utf-8")).get("rows", 0)
               for path in manifests)
    failures_path = directory / "fallos.json"
    failures = len(json.loads(failures_path.read_text(encoding="utf-8"))) if failures_path.exists() else "pendiente"
    print(f"{name}: {len(manifests)}/{expected} partes terminadas; {rows:,} registros; "
          f"fallos en último intento: {failures}")


def main() -> None:
    symbols, excluded = stocks(RAW / "alpaca_activos.json")
    batches = (len(symbols) + 49) // 50
    print(f"Catálogo: {len(symbols):,} símbolos consultables; {len(excluded):,} excluidos")
    summary("barras_diarias", batches)
    summary("subastas", batches)
    summary("noticias", len(periods("news", END)))
    summary("acciones_corporativas", len(periods("actions", END)))
    snapshots = ROOT / "estado_actual"
    active = sum(1 for item in json.loads((RAW / "alpaca_activos.json").read_text(encoding="utf-8"))
                 if item.get("status") == "active" and item.get("exchange") != "OTC"
                 and item.get("class") == "us_equity"
                 and re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", item.get("symbol", "")))
    print(f"estado_actual: {len(list(snapshots.glob('captura_*.json')))}/{(active + 49) // 50} capturas")


if __name__ == "__main__":
    main()
