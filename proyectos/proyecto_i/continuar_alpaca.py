"""Espera a los descargadores activos y reintenta las colecciones incompletas.

Ejecutar desde la carpeta proyecto_i con `nohup python3 -u continuar_alpaca.py
> data/raw/masivo/supervisor.log 2>&1 &`. No almacena credenciales.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import subprocess
import sys
import time

from descargar_alpaca_eventos import periods
from descargar_alpaca_masivo import stocks


HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
ROOT = RAW / "masivo"
END = "2026-09-28"


def log(message: str) -> None:
    print(f"{datetime.now(timezone.utc).isoformat()} {message}", flush=True)


def active(script: str, mode: str | None = None) -> bool:
    result = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, check=True)
    current = str(Path(__file__).resolve())
    for line in result.stdout.splitlines():
        if script not in line or current in line:
            continue
        if mode is None or f" {mode} " in f" {line} ":
            return True
    return False


def completed(folder: str) -> int:
    return len(list((ROOT / folder).glob("*.manifest.json")))


def run_until_complete(folder: str, expected: int, command: list[str], script: str,
                       mode: str | None = None) -> None:
    while active(script, mode):
        log(f"{folder}: esperando al proceso inicial ({completed(folder)}/{expected})")
        time.sleep(60)
    for attempt in range(1, 4):
        count = completed(folder)
        if count >= expected:
            log(f"{folder}: completo ({count}/{expected})")
            return
        log(f"{folder}: intento {attempt}, {count}/{expected} partes completas")
        result = subprocess.run(command, cwd=HERE, check=False)
        count = completed(folder)
        log(f"{folder}: código {result.returncode}; {count}/{expected} partes completas")
        if count >= expected:
            return
        time.sleep(30 * attempt)
    log(f"{folder}: INCOMPLETO; revisar fallos.json y supervisor.log")


def main() -> None:
    symbols, _ = stocks(RAW / "alpaca_activos.json")
    batches = (len(symbols) + 49) // 50
    python = sys.executable
    run_until_complete("barras_diarias", batches,
                       [python, str(HERE / "descargar_alpaca_masivo.py"), "--kind", "bars", "--end", END],
                       "descargar_alpaca_masivo.py")
    run_until_complete("subastas", batches,
                       [python, str(HERE / "descargar_alpaca_masivo.py"), "--kind", "auctions", "--end", END],
                       "descargar_alpaca_masivo.py")
    news_months = len(periods("news", date.fromisoformat(END)))
    run_until_complete("noticias", news_months,
                       [python, str(HERE / "descargar_alpaca_eventos.py"), "news", "--end", END,
                        "--workers", "2", "--delay", "1.2"],
                       "descargar_alpaca_eventos.py", "news")
    log("Resumen final:")
    subprocess.run([python, str(HERE / "estado_alpaca.py")], cwd=HERE, check=False)


if __name__ == "__main__":
    main()
