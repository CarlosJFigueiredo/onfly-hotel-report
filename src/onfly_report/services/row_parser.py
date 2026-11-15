"""Conversão de uma linha do CSV para o modelo de reserva."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import TypeVar

from ..exceptions import InputFileError
from ..models import RawRow, Reservation

T = TypeVar("T")


def _text(raw: RawRow, column: str) -> str:
    return (raw.values.get(column) or "").strip()


def _convert(raw: RawRow, column: str, convert: Callable[[str], T]) -> T:
    """Converte o valor da coluna; a falha indica linha, coluna e valor recebido."""
    value = _text(raw, column)
    try:
        return convert(value)
    except (ValueError, InvalidOperation) as err:
        raise InputFileError(f"linha {raw.line_number}: valor inválido em {column}: {value!r}") from err


class RowParser:
    """Converte a linha crua em Reservation.

    O arquivo de entrada é consistente; falhas de formato são erro de arquivo, não dado a
    ser descartado.
    """

    def parse(self, raw: RawRow) -> Reservation:
        return Reservation(
            reservation_id=_text(raw, "reservation_id"),
            traveler_name=_text(raw, "traveler_name"),
            company_id=_text(raw, "company_id"),
            hotel_id=_text(raw, "hotel_id"),
            hotel_name=_text(raw, "hotel_name"),
            city=_text(raw, "city"),
            country=_text(raw, "country"),
            checkin=_convert(raw, "checkin_date", date.fromisoformat),
            checkout=_convert(raw, "checkout_date", date.fromisoformat),
            rooms=_convert(raw, "rooms", int),
            status=_text(raw, "status"),
            currency=_text(raw, "currency").upper(),
            amount=_convert(raw, "amount", Decimal),
            payment_method=_text(raw, "payment_method"),
            line_number=raw.line_number,
        )
