"""Construção do relatório consolidado.

`aggregate` calcula os totais com valores exatos; `serialize` aplica o contrato JSON (ordenação,
corte do `--top` e arredondamento half-up). `ReportBuilder` orquestra a leitura e as duas etapas.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from ..models import Reservation
from ..repositories.csv_rate_repository import CsvRateRepository
from ..repositories.csv_reservation_repository import CsvReservationRepository
from .currency_converter import convert_to_brl
from .row_parser import RowParser
from .status_policy import is_billable
from .stay_calculator import calculate_room_nights

REPORT_VERSION = "1.0"
MONEY_QUANTUM = Decimal("0.01")
FIXED_OFFSET = timezone(timedelta(hours=-3))


def format_money(value: Decimal) -> str:
    """Serializa dinheiro com duas casas, arredondamento half-up."""
    return str(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP))


@dataclass
class Totals:
    """Acumula reservas, noites e valor exato em BRL de um grupo de reservas."""

    reservations: int = 0
    room_nights: int = 0
    amount: Decimal = Decimal("0")

    def add(self, room_nights: int, amount: Decimal) -> None:
        self.reservations += 1
        self.room_nights += room_nights
        self.amount += amount

    @property
    def average_nightly_rate(self) -> Decimal:
        """Valor por noite; sem noites, zero."""
        return self.amount / self.room_nights if self.room_nights else Decimal("0")


@dataclass(frozen=True)
class Aggregation:
    """Resultado da agregação: contagens e totais exatos, ainda sem ordenação nem arredondamento."""

    total_reservations: int
    status_counts: Counter[str]
    overall: Totals
    by_month: dict[str, Totals]
    by_hotel: dict[str, Totals]
    hotel_names: dict[str, str]


def aggregate(reservations: list[Reservation], rates: dict[str, Decimal]) -> Aggregation:
    """Conta os status de todas as reservas e soma noites e valores apenas das faturáveis."""
    status_counts = Counter(reservation.status for reservation in reservations)
    billable = [reservation for reservation in reservations if is_billable(reservation.status)]

    overall = Totals()
    by_month: defaultdict[str, Totals] = defaultdict(Totals)
    by_hotel: defaultdict[str, Totals] = defaultdict(Totals)
    hotel_names: dict[str, str] = {}

    for reservation in billable:
        room_nights = calculate_room_nights(reservation.checkin, reservation.checkout, reservation.rooms)
        amount_brl = convert_to_brl(reservation.amount, reservation.currency, rates)

        overall.add(room_nights, amount_brl)
        by_month[reservation.checkin.strftime("%Y-%m")].add(room_nights, amount_brl)
        by_hotel[reservation.hotel_id].add(room_nights, amount_brl)
        hotel_names[reservation.hotel_id] = reservation.hotel_name

    return Aggregation(
        total_reservations=len(reservations),
        status_counts=status_counts,
        overall=overall,
        by_month=dict(by_month),
        by_hotel=dict(by_hotel),
        hotel_names=hotel_names,
    )


def serialize(aggregation: Aggregation, top_n: int, generated_at: datetime) -> dict:
    """Monta o relatório no formato do contrato; o dinheiro é arredondado somente aqui."""
    overall = aggregation.overall
    ranked_hotels = sorted(aggregation.by_hotel.items(), key=lambda item: (-item[1].amount, item[0]))

    return {
        "report_version": REPORT_VERSION,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "summary": {
            "total_reservations": aggregation.total_reservations,
            "confirmed_reservations": aggregation.status_counts["CONFIRMED"],
            "cancelled_reservations": aggregation.status_counts["CANCELLED"],
            "no_show_reservations": aggregation.status_counts["NO_SHOW"],
            "total_room_nights": overall.room_nights,
            "total_amount_brl": format_money(overall.amount),
            "average_nightly_rate_brl": format_money(overall.average_nightly_rate),
        },
        "by_month": [
            {
                "month": month,
                "reservations": totals.reservations,
                "room_nights": totals.room_nights,
                "total_brl": format_money(totals.amount),
            }
            for month, totals in sorted(aggregation.by_month.items())
        ],
        "top_hotels": [
            {
                "hotel_id": hotel_id,
                "hotel_name": aggregation.hotel_names[hotel_id],
                "room_nights": totals.room_nights,
                "total_brl": format_money(totals.amount),
            }
            for hotel_id, totals in ranked_hotels[:top_n]
        ],
    }


class ReportBuilder:
    """Orquestra leitura, conversão de tipos, agregação e serialização."""

    def __init__(
        self,
        reservation_repository: CsvReservationRepository,
        rate_repository: CsvRateRepository,
        top_n: int = 5,
        now: datetime | None = None,
    ) -> None:
        self._reservation_repository = reservation_repository
        self._rate_repository = rate_repository
        self._top_n = top_n
        self._now = now

    def build(self) -> dict:
        parser = RowParser()
        reservations = [parser.parse(raw) for raw in self._reservation_repository.read()]
        rates = self._rate_repository.read()
        generated_at = self._now or datetime.now(FIXED_OFFSET)
        return serialize(aggregate(reservations, rates), self._top_n, generated_at)
