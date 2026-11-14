"""Apoio aos testes adicionais: executa o CLI sem exigir sucesso.

O `helpers.run_cli` fornecido sempre passa `--top`/`--output` e exige código de saída 0.
Os testes de erro e de argumentos padrão precisam controlar a linha de comando e inspecionar
o processo, então este módulo complementa o helper sem alterá-lo.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

from helpers import BASE, COLUMNS, PROJECT_ROOT, SRC_DIR

DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_RATES = "currency,rate_to_brl\nBRL,1.000000\nUSD,5.420000\nEUR,5.880000\n"


def write_reservations(path: Path, rows: list[dict[str, str]], columns: list[str] = COLUMNS) -> Path:
    """Grava um CSV de reservas completando cada linha com os valores de `helpers.BASE`."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({**BASE, **row} for row in rows)
    return path


def write_rates(path: Path, content: str = DEFAULT_RATES) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def run_cli_process(args: list[str], cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    """Executa `python -m onfly_report` com os argumentos dados e devolve o processo concluído."""
    environment = os.environ.copy()
    for import_root in (SRC_DIR, PROJECT_ROOT):
        if (import_root / "onfly_report").is_dir():
            environment["PYTHONPATH"] = str(import_root) + os.pathsep + environment.get("PYTHONPATH", "")
            break
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run(
        [sys.executable, "-m", "onfly_report", *args],
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
