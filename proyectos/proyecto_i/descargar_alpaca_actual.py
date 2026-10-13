"""Capturas actuales y códigos de referencia de acciones de EE. UU. con Alpaca CLI.

Una captura es una observación puntual, no un histórico. Solo se consultan
activos vigentes no OTC, pues los inactivos no tienen cotización actual.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import time


RAW = Path(__file__).parent / "data" / "raw"
OUT = RAW / "masivo" / "estado_actual"


def call(*parts: str) -> dict:
    command = ["alpaca", "data", *parts, "--timeout", "90"]
    for attempt in range(5):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            value = json.loads(result.stdout)
            if not isinstance(value, dict):
                raise ValueError("Respuesta inesperada de Alpaca")
            return value
        error = result.stderr.strip()
        if not any(term in error.lower() for term in (
            "no such host", "timeout", "timed out", "connection reset", "429", "500", "502", "503", "504",
        )) or attempt == 4:
            raise RuntimeError(error)
        time.sleep(min(2 ** attempt, 16))
    raise AssertionError("bucle de reintentos sin resultado")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assets = json.loads((RAW / "alpaca_activos.json").read_text(encoding="utf-8"))
    symbols = sorted({item["symbol"] for item in assets
                      if item.get("class") == "us_equity" and item.get("status") == "active"
                      and item.get("exchange") != "OTC"
                      and re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", item.get("symbol", ""))})
    failures = []
    for index in range(0, len(symbols), 50):
        batch = symbols[index:index + 50]
        path = OUT / f"captura_{index // 50:04d}.json"
        if path.exists():
            continue
        try:
            response = call("multi-snapshots", "--symbols", ",".join(batch), "--feed", "iex")
        except (OSError, RuntimeError, ValueError) as exc:
            failures.append({"batch": index // 50, "error": str(exc)})
            print(f"captura {index // 50}: {exc}", flush=True)
            if len(failures) >= 3:
                break
            continue
        path.write_text(json.dumps({"downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                                    "feed": "iex", "requested_symbols": batch,
                                    "snapshots": response}, ensure_ascii=False) + "\n", encoding="utf-8")
        if index % 500 == 0:
            print(f"capturas: {index + len(batch)}/{len(symbols)}", flush=True)
        time.sleep(0.35)
    references = [("exchanges", ("meta", "exchanges"))]
    references.extend(
        (f"{ticktype}_conditions_{tape}",
         ("meta", "conditions", "--ticktype", ticktype, "--tape", tape))
        for ticktype in ("trade", "quote") for tape in ("A", "B", "C")
    )
    for name, parts in references:
        path = OUT / f"{name}.json"
        if not path.exists():
            try:
                path.write_text(json.dumps(call(*parts), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except (OSError, RuntimeError, ValueError) as exc:
                failures.append({"reference": name, "error": str(exc)})
    (OUT / "fallos.json").write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    snapshots = [json.loads(path.read_text(encoding="utf-8"))
                 for path in sorted(OUT.glob("captura_*.json"))]
    returned = {symbol for item in snapshots for symbol in item["snapshots"]}
    summary = {"requested_symbols": len(symbols), "returned_snapshots": len(returned),
               "without_snapshot": sorted(set(symbols) - returned),
               "completed_batches": len(snapshots), "expected_batches": (len(symbols) + 49) // 50,
               "failed_requests": len(failures)}
    (OUT / "resumen.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Solicitados: {len(symbols)}; capturas: {len(returned)}; fallos: {len(failures)}", flush=True)


if __name__ == "__main__":
    main()
