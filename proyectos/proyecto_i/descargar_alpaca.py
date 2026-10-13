"""Descarga barras históricas de acciones con la CLI oficial de Alpaca.

Requiere una sesión creada previamente con ``alpaca profile login``.
Guarda un CSV para pandas y un JSONL que conserva todos los campos de la API.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


FIELDS = {
    "t": "timestamp",
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
    "n": "trade_count",
    "vw": "vwap",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", required=True, help="Símbolos separados por comas")
    parser.add_argument("--start", required=True, help="Fecha inicial YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="Fecha final YYYY-MM-DD")
    parser.add_argument("--feed", choices=("sip", "iex"), default="sip")
    parser.add_argument("--adjustment", choices=("raw", "split", "all"), default="split")
    parser.add_argument("--min-rows", type=int, default=10_000)
    parser.add_argument("--profile", help="Perfil configurado en la CLI de Alpaca")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "data" / "raw" / "alpaca_barras.csv",
    )
    args = parser.parse_args()
    if date.fromisoformat(args.start) > date.fromisoformat(args.end):
        parser.error("--start debe ser anterior o igual a --end")
    if args.min_rows < 1:
        parser.error("--min-rows debe ser positivo")
    return args


def fetch_page(args: argparse.Namespace, symbols: list[str], token: str | None) -> dict:
    command = [
        "alpaca", "data", "multi-bars",
        "--symbols", ",".join(symbols),
        "--start", args.start,
        "--end", args.end,
        "--timeframe", "1Day",
        "--feed", args.feed,
        "--adjustment", args.adjustment,
        "--limit", "10000",
        "--timeout", "60",
    ]
    if token:
        command.extend(("--page-token", token))
    if args.profile:
        command.extend(("--profile", args.profile))
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Alpaca terminó con código {result.returncode}")
    response = json.loads(result.stdout)
    if not isinstance(response, dict) or not isinstance(response.get("bars"), dict):
        raise ValueError("Respuesta inesperada de alpaca data multi-bars")
    return response


def download(args: argparse.Namespace) -> tuple[int, int, Path, Path]:
    symbols = list(dict.fromkeys(s.strip().upper() for s in args.symbols.split(",") if s.strip()))
    if not symbols:
        raise ValueError("Debes indicar al menos un símbolo")

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = output.with_suffix(".jsonl")
    temporary: list[Path] = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=output.parent, delete=False) as csv_file, \
             tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as jsonl_file:
            temporary = [Path(csv_file.name), Path(jsonl_file.name)]
            writer = csv.DictWriter(csv_file, fieldnames=["symbol", *FIELDS.values()])
            writer.writeheader()
            count = pages = 0
            token = None
            seen_tokens: set[str] = set()
            while True:
                response = fetch_page(args, symbols, token)
                pages += 1
                for symbol, bars in response["bars"].items():
                    if not isinstance(bars, list):
                        raise ValueError(f"Formato de barras inesperado para {symbol}")
                    for bar in bars:
                        if not isinstance(bar, dict):
                            raise ValueError(f"Barra inesperada para {symbol}")
                        writer.writerow({"symbol": symbol, **{name: bar.get(key) for key, name in FIELDS.items()}})
                        jsonl_file.write(json.dumps({"symbol": symbol, **bar}, ensure_ascii=False) + "\n")
                        count += 1
                token = response.get("next_page_token")
                print(f"Página {pages}: {count} barras acumuladas", file=sys.stderr)
                if not token:
                    break
                if not isinstance(token, str) or token in seen_tokens:
                    raise ValueError("Token de paginación inválido o repetido")
                seen_tokens.add(token)

        if count < args.min_rows:
            raise ValueError(f"Solo se descargaron {count} barras; mínimo solicitado: {args.min_rows}")
        os.replace(temporary[0], output)
        os.replace(temporary[1], jsonl_path)
        metadata = {
            "source": "https://data.alpaca.markets/v2/stocks/bars",
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "symbols": symbols,
            "start": args.start,
            "end": args.end,
            "timeframe": "1Day",
            "feed": args.feed,
            "adjustment": args.adjustment,
            "rows": count,
            "pages": pages,
            "csv": output.name,
            "jsonl": jsonl_path.name,
        }
        output.with_suffix(".manifest.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return count, pages, output, jsonl_path
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def main() -> int:
    try:
        args = parse_args()
        count, pages, csv_path, jsonl_path = download(args)
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Descargadas {count} barras en {pages} páginas. CSV: {csv_path}; JSONL: {jsonl_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
