"""-> Descarga reanudable de noticias y acciones corporativas con la CLI de Alpaca."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


RAW = Path(__file__).parent / "data" / "raw" / "masivo"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("news", "actions"))
    parser.add_argument("--end", required=True, help="Último día ya completado, YYYY-MM-DD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-periods", type=int, help="Para pruebas parciales")
    parser.add_argument("--workers", type=int, default=3, help="Periodos simultáneos; acciones usa 1")
    parser.add_argument("--delay", type=float, help="Pausa entre páginas de cada trabajador")
    parser.add_argument("--max-gb", type=float, default=50)
    parser.add_argument("--min-free-gb", type=float, default=20)
    args = parser.parse_args()
    args.output = args.output or RAW / ("noticias" if args.mode == "news" else "acciones_corporativas")
    args.delay = args.delay if args.delay is not None else (1.2 if args.mode == "news" else 0.6)
    if args.workers < 1:
        parser.error("--workers debe ser positivo")
    if args.delay < 0:
        parser.error("--delay no puede ser negativo")
    return args


def periods(mode: str, final: date) -> list[tuple[str, str, str]]:
    result = []
    if mode == "news":
        year, month = 2015, 1
        while date(year, month, 1) <= final:
            next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
            start = date(year, month, 1)
            end = min(date(next_year, next_month, 1), final + timedelta(days=1))
            result.append((f"{year:04d}-{month:02d}", start.isoformat() + "T00:00:00Z", end.isoformat() + "T00:00:00Z"))
            year, month = next_year, next_month
    else:
        spans = [("1900-1999", date(1900, 1, 1), date(1999, 12, 31)),
                 ("2000-2009", date(2000, 1, 1), date(2009, 12, 31))]
        spans.extend((str(year), date(year, 1, 1), date(year, 12, 31)) for year in range(2010, final.year + 1))
        result = [(name, start.isoformat(), min(end, final).isoformat()) for name, start, end in spans if start <= final]
    return result


def fetch(mode: str, start: str, end: str, token: str | None) -> dict:
    if mode == "news":
        command = ["alpaca", "data", "news", "--start", start, "--end", end,
                   "--sort", "asc", "--limit", "50", "--include-content", "--timeout", "90"]
    else:
        command = ["alpaca", "data", "corporate-actions", "--start", start, "--end", end,
                   "--sort", "asc", "--limit", "1000", "--data-quality", "all", "--timeout", "90"]
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
    if not isinstance(response, dict):
        raise ValueError("Respuesta inesperada")
    return response


def rows(mode: str, response: dict):
    if mode == "news":
        news = response.get("news")
        if not isinstance(news, list):
            raise ValueError("Formato de noticias inesperado")
        for item in news:
            yield item
    else:
        groups = response.get("corporate_actions")
        if not isinstance(groups, dict):
            raise ValueError("Formato de acciones corporativas inesperado")
        for category, items in groups.items():
            for item in items:
                yield {"category": category, **item}


def download_period(args: argparse.Namespace, name: str, start: str, end: str) -> dict:
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    data_path = output / f"{name}.jsonl.gz"
    manifest_path = output / f"{name}.manifest.json"
    if data_path.exists() and manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (previous.get("mode"), previous.get("start"), previous.get("end")) != (args.mode, start, end):
            raise ValueError(f"El periodo {name} existente usa parámetros distintos")
        return previous
    free_gb = shutil.disk_usage(output).free / 1_000_000_000
    used_gb = sum(path.stat().st_size for path in output.glob("*.jsonl.gz")) / 1_000_000_000
    if free_gb < args.min_free_gb or used_gb >= args.max_gb:
        raise RuntimeError(f"Límite de disco: libre={free_gb:.1f} GB; descarga={used_gb:.1f} GB")

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output, suffix=".jsonl.gz", delete=False) as handle:
            temporary = Path(handle.name)
        count = pages = 0
        token = None
        seen_tokens = set()
        with gzip.open(temporary, "wt", encoding="utf-8") as sink:
            while True:
                response = fetch(args.mode, start, end, token)
                pages += 1
                for item in rows(args.mode, response):
                    sink.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
                    count += 1
                token = response.get("next_page_token")
                time.sleep(args.delay)
                if not token:
                    break
                if not isinstance(token, str) or token in seen_tokens:
                    raise ValueError("Token de página repetido o inválido")
                seen_tokens.add(token)
        manifest = {
            "mode": args.mode, "period": name, "start": start, "end": end,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "rows": count, "pages": pages,
            "source": ("https://data.alpaca.markets/v1beta1/news" if args.mode == "news"
                       else "https://data.alpaca.markets/v1/corporate-actions"),
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
    final = date.fromisoformat(args.end)
    intervals = periods(args.mode, final)
    print(f"{args.mode}: {len(intervals)} periodos", flush=True)
    failures = []
    chosen = intervals[:args.max_periods] if args.max_periods is not None else intervals
    workers = args.workers if args.mode == "news" else 1
    consecutive_failures = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for offset in range(0, len(chosen), workers):
            pending = {
                pool.submit(download_period, args, name, start, end): (index, name)
                for index, (name, start, end) in enumerate(chosen[offset:offset + workers], offset)
            }
            for future in as_completed(pending):
                index, name = pending[future]
                try:
                    manifest = future.result()
                except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                    failures.append({"period": name, "error": str(exc)})
                    print(f"{name}: ERROR {exc}", file=sys.stderr, flush=True)
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0
                    print(f"{name} ({index + 1}/{len(intervals)}): {manifest['rows']} registros, {manifest['pages']} páginas", flush=True)
            if consecutive_failures >= 3 or any("Límite de disco" in item["error"] for item in failures):
                break
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "fallos.json").write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
