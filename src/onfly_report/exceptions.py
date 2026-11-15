"""Exceções de domínio do consolidador de reservas.

Toda `DomainError` representa entrada inválida: o CLI mostra a mensagem, sem traceback, e encerra
com código 2. Qualquer outra exceção é tratada como erro inesperado (código 1).
"""

from __future__ import annotations

from collections.abc import Iterable


class DomainError(Exception):
    """Erro de entrada inválida (código de saída 2)."""


class InputFileError(DomainError):
    """Arquivo de entrada ausente, ilegível ou fora do formato esperado."""


class MissingRateError(DomainError):
    """Reserva em uma moeda sem taxa de câmbio cadastrada."""

    def __init__(self, currency: str, available: Iterable[str]) -> None:
        self.currency = currency
        super().__init__(
            f"moeda sem taxa de câmbio cadastrada: {currency} (disponíveis: {', '.join(sorted(available))})"
        )
