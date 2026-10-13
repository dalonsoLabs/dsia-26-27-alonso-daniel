"""Descarga reanudable de barras y subastas de activos de EE. UU. mediante Alpaca.

Cada lote se escribe en JSONL comprimido y recibe un manifiesto solo al completarse.
Los activos OTC se excluyen porque el perfil normal no tiene acceso a su feed.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("bars", "auctions"), default="bars")
    parser.add_argument("--assets", type=Path, default=RAW / "alpaca_activos.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--start", default="2016-01-01")
    parser.add_argument("--end", required=True, help="Último día de mercado ya finalizado")
    parser.add_argument("--feed", choices=("sip", "iex"), default="sip")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--max-batches", type=int, help="Para una prueba parcial; omitir para todos")
    parser.add_argument("--max-gb", type=float, default=50)
    parser.add_argument("--min-free-gb", type=float, default=20)
    args = parser.parse_args()
    args.output = args.output or RAW / "masivo" / ("barras_diarias" if args.kind == "bars" else "subastas")
    if args.batch_size < 1 or args.max_gb <= 0 or args.min_free_gb <= 0:
        parser.error("Los tamaños y límites deben ser positivos")
    return args


def stocks(assets_path: Path) -> tuple[list[str], list[dict]]:
    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    selected = set()
    excluded = []
    for item in assets:
        if item.get("class") != "us_equity" or not item.get("symbol"):
            continue
        symbol = item["symbol"]
        reason = None
        if item.get("exchange") == "OTC":
            reason = "OTC: feed no disponible en este perfil"
        elif not re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", symbol):
            reason = "identificador no válido como ticker de barras"
        if reason:
            excluded.append({"symbol": symbol, "exchange": item.get("exchange"), "reason": reason})
        else:
            selected.add(symbol)
    return sorted(selected), excluded


def page(args: argparse.Namespace, symbols: list[str], token: str | None) -> dict:
    command = [
        "alpaca", "data", "multi-bars" if args.kind == "bars" else "auctions",
        "--symbols", ",".join(symbols),
        "--start", args.start,
        "--end", args.end,
        "--feed", args.feed,
        "--limit", "10000",
        "--timeout", "90",
    ]
    if args.kind == "bars":
        command.extend(("--timeframe", "1Day", "--adjustment", "split"))
    if token:
        command.extend(("--page-token", token))
    for attempt in range(5):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if not result.returncode:
            break
        error = result.stderr.strip() or f"CLI terminó con código {result.returncode}"
        transient = any(part in error.lower() for part in (
            "no such host", "timeout", "timed out", "connection reset",
            "could not reach", "connection refused", "429", "500", "502", "503", "504",
        ))
        if not transient or attempt == 4:
            raise RuntimeError(error)
        time.sleep(min(2 ** attempt, 16))
    response = json.loads(result.stdout)
    if not isinstance(response, dict) or not isinstance(response.get(args.kind), dict):
        raise ValueError(f"Respuesta de {args.kind} inesperada")
    return response


def check_space(args: argparse.Namespace, output: Path) -> None:
    free_gb = shutil.disk_usage(output).free / 1_000_000_000
    used_gb = sum(path.stat().st_size for path in output.glob("*.jsonl.gz")) / 1_000_000_000
    if free_gb < args.min_free_gb or used_gb >= args.max_gb:
        raise RuntimeError(f"Límite de disco: libre={free_gb:.1f} GB; descarga={used_gb:.1f} GB")


def batch(args: argparse.Namespace, number: int, symbols: list[str]) -> dict:
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    stem = f"lote_{number:04d}"
    data_path = output / f"{stem}.jsonl.gz"
    manifest_path = output / f"{stem}.manifest.json"
    if manifest_path.exists() and data_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (previous.get("requested_symbols") != symbols
                or previous.get("kind", "bars") != args.kind
                or previous.get("start") != args.start
                or previous.get("end") != args.end
                or previous.get("feed") != args.feed):
            raise ValueError(f"El lote {number} existente usa parámetros distintos")
        return previous

    check_space(args, output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output, suffix=".jsonl.gz", delete=False) as handle:
            temporary = Path(handle.name)
        count = pages = 0
        by_symbol: Counter[str] = Counter()
        query_symbols = list(symbols)
        rejected_symbols = []
        token = None
        seen_tokens: set[str] = set()
        with gzip.open(temporary, "wt", encoding="utf-8") as sink:
            while query_symbols:
                try:
                    response = page(args, query_symbols, token)
                except RuntimeError as exc:
                    invalid = re.search(r"invalid symbol: ([A-Z0-9.]+)", str(exc))
                    if token is not None or invalid is None or invalid.group(1) not in query_symbols:
                        raise
                    rejected_symbols.append(invalid.group(1))
                    query_symbols.remove(invalid.group(1))
                    print(f"Lote {number}: símbolo rechazado por Alpaca: {invalid.group(1)}", file=sys.stderr, flush=True)
                    continue
                pages += 1
                for symbol, records in response[args.kind].items():
                    if not isinstance(records, list):
                        raise ValueError(f"Registros inesperados para {symbol}")
                    for record in records:
                        sink.write(json.dumps({"symbol": symbol, **record}, separators=(",", ":")) + "\n")
                        count += 1
                        by_symbol[symbol] += 1
                token = response.get("next_page_token")
                time.sleep(0.35)  # por debajo de 200 llamadas/minuto del plan Basic
                if not token:
                    break
                if not isinstance(token, str) or token in seen_tokens:
                    raise ValueError("Token de página repetido o inválido")
                seen_tokens.add(token)
        manifest = {
            "source": f"https://data.alpaca.markets/v2/stocks/{args.kind}",
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "kind": args.kind,
            "batch": number,
            "requested_symbols": symbols,
            "rejected_symbols": rejected_symbols,
            "returned_symbols": dict(by_symbol),
            "rows": count,
            "pages": pages,
            "start": args.start,
            "end": args.end,
            "feed": args.feed,
            "timeframe": "1Day" if args.kind == "bars" else None,
            "adjustment": "split" if args.kind == "bars" else None,
            "data_file": data_path.name,
        }
        os.replace(temporary, data_path)
        temporary = None
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    args = arguments()
    symbols, excluded = stocks(args.assets)
    batches = [symbols[i:i + args.batch_size] for i in range(0, len(symbols), args.batch_size)]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "activos_no_consultados.json").write_text(
        json.dumps(excluded, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Símbolos consultables: {len(symbols)}; excluidos: {len(excluded)}; lotes: {len(batches)}", flush=True)
    failures = []
    consecutive_failures = 0
    for index, group in enumerate(batches):
        if args.max_batches is not None and index >= args.max_batches:
            break
        try:
            manifest = batch(args, index, group)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            failures.append({"batch": index, "symbols": group, "error": str(exc)})
            print(f"Lote {index}: ERROR {exc}", file=sys.stderr, flush=True)
            consecutive_failures += 1
            if "Límite de disco" in str(exc) or consecutive_failures >= 3:
                break
        else:
            consecutive_failures = 0
            print(f"Lote {index + 1}/{len(batches)}: {manifest['rows']} barras, {manifest['pages']} páginas", flush=True)
    failure_path = args.output.expanduser().resolve() / "fallos.json"
    failure_path.write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
