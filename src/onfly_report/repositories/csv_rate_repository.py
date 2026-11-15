"""Leitura da tabela de câmbio para BRL."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..exceptions import InputFileError
from ._csv import read_csv

REQUIRED_COLUMNS = ("currency", "rate_to_brl")


class CsvRateRepository:
    """Carrega moeda -> taxa para BRL a partir de um CSV."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> dict[str, Decimal]:
        rates: dict[str, Decimal] = {}
        for row in read_csv(self._path, REQUIRED_COLUMNS):
            currency = (row.values.get("currency") or "").strip().upper()
            raw_rate = (row.values.get("rate_to_brl") or "").strip()
            if not currency or not raw_rate:
                raise InputFileError(f"linha de câmbio incompleta em {self._path}")
            try:
                rate = Decimal(raw_rate)
            except InvalidOperation as err:
                raise InputFileError(f"taxa inválida para {currency} em {self._path}") from err
            if rate <= 0:
                raise InputFileError(f"taxa não positiva para {currency} em {self._path}")
            rates[currency] = rate

        if not rates:
            raise InputFileError(f"tabela de câmbio vazia: {self._path}")
        return rates
