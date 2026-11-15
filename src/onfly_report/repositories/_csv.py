"""Leitura de CSV compartilhada pelos repositórios."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from ..exceptions import InputFileError
from ..models import RawRow


def read_csv(path: Path, required_columns: Sequence[str]) -> list[RawRow]:
    """Lê um CSV, valida o cabeçalho e devolve as linhas com o número da linha física.

    As exportações alinham as colunas com espaços (ex.: `, "Hotel Lisboa, Centro"  ,`).
    `skipinitialspace` descarta o espaço após a vírgula, para que as aspas sejam reconhecidas e a
    vírgula interna não divida o campo; o cabeçalho tem os espaços removidos. Os valores voltam
    como lidos: a limpeza e a conversão ficam com quem os consome.
    """
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, skipinitialspace=True)
            fieldnames = [name.strip() for name in (reader.fieldnames or [])]
            reader.fieldnames = fieldnames
            missing = [column for column in required_columns if column not in fieldnames]
            if missing:
                raise InputFileError(f"colunas obrigatórias ausentes em {path}: {', '.join(missing)}")
            return [RawRow(line_number=reader.line_num, values=values) for values in reader]
    except FileNotFoundError as err:
        raise InputFileError(f"arquivo não encontrado: {path}") from err
    except (OSError, csv.Error) as err:
        raise InputFileError(f"falha ao ler {path}: {err}") from err
