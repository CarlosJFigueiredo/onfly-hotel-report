"""Testes adicionais: contrato do relatório e do CLI descrito no README."""

import json
import re
from datetime import datetime, timedelta

from cli_support import run_cli_process, write_rates, write_reservations
from helpers import run_cli

MONEY = re.compile(r"\d+\.\d{2}")


def test_report_follows_readme_schema(tmp_path):
    """Campos, tipos e formatos exatamente como no README; dinheiro com 2 casas e sem separador de milhar."""
    report = run_cli(tmp_path, [{"reservation_id": "R-1", "amount": "1234567.8"}])

    assert set(report) == {"report_version", "generated_at", "summary", "by_month", "top_hotels"}
    assert report["report_version"] == "1.0"
    assert datetime.fromisoformat(report["generated_at"]).utcoffset() == timedelta(hours=-3)

    summary = report["summary"]
    assert set(summary) == {
        "total_reservations",
        "confirmed_reservations",
        "cancelled_reservations",
        "no_show_reservations",
        "total_room_nights",
        "total_amount_brl",
        "average_nightly_rate_brl",
    }
    for field in (
        "total_reservations",
        "confirmed_reservations",
        "cancelled_reservations",
        "no_show_reservations",
        "total_room_nights",
    ):
        assert type(summary[field]) is int, field
    assert summary["total_amount_brl"] == "1234567.80"
    assert MONEY.fullmatch(summary["average_nightly_rate_brl"])

    [month] = report["by_month"]
    assert set(month) == {"month", "reservations", "room_nights", "total_brl"}
    assert re.fullmatch(r"\d{4}-\d{2}", month["month"])
    assert type(month["reservations"]) is int and type(month["room_nights"]) is int
    assert MONEY.fullmatch(month["total_brl"])

    [hotel] = report["top_hotels"]
    assert set(hotel) == {"hotel_id", "hotel_name", "room_nights", "total_brl"}
    assert type(hotel["hotel_id"]) is str and type(hotel["hotel_name"]) is str
    assert type(hotel["room_nights"]) is int
    assert MONEY.fullmatch(hotel["total_brl"])


def test_optional_arguments_use_documented_defaults(tmp_path):
    """Sem `--output` e `--top`: grava em output/report.json (criando o diretório) com 5 hotéis no ranking."""
    rows = [
        {"reservation_id": f"R-{index}", "hotel_id": f"H0{index}", "amount": f"{index}00.00"} for index in range(1, 7)
    ]
    input_csv = write_reservations(tmp_path / "reservas.csv", rows)
    rates_csv = write_rates(tmp_path / "rates.csv")

    process = run_cli_process(["--input", str(input_csv), "--rates", str(rates_csv)], cwd=tmp_path)

    assert process.returncode == 0, process.stderr
    report = json.loads((tmp_path / "output" / "report.json").read_text(encoding="utf-8"))
    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H06", "H05", "H04", "H03", "H02"]
