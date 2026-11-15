"""Leitura da exportação de reservas em CSV."""

from __future__ import annotations

from pathlib import Path

from ..models import RawRow
from ._csv import read_csv

REQUIRED_COLUMNS = (
    "reservation_id",
    "traveler_name",
    "company_id",
    "hotel_id",
    "hotel_name",
    "city",
    "country",
    "checkin_date",
    "checkout_date",
    "rooms",
    "status",
    "currency",
    "amount",
    "payment_method",
    "booked_at",
)


class CsvReservationRepository:
    """Lê a exportação de reservas sem aplicar regra de negócio."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> list[RawRow]:
        return read_csv(self._path, REQUIRED_COLUMNS)
