"""Testes adicionais: normalização do código de moeda e moeda sem taxa de câmbio."""

from cli_support import run_cli_process, write_rates, write_reservations
from helpers import run_cli


def test_currency_code_is_case_insensitive(tmp_path):
    """A moeda da reserva é normalizada para maiúsculas, como na tabela de câmbio."""
    report = run_cli(tmp_path, [{"reservation_id": "R-1", "currency": "usd", "amount": "100.00"}])
    assert report["summary"]["total_amount_brl"] == "542.00"


def test_currency_without_rate_is_invalid_input(tmp_path):
    """Moeda ausente da tabela de câmbio é entrada inválida: código 2, sem traceback e sem relatório."""
    input_csv = write_reservations(tmp_path / "reservas.csv", [{"currency": "GBP"}])
    rates_csv = write_rates(tmp_path / "rates.csv")
    output = tmp_path / "report.json"

    process = run_cli_process(["--input", str(input_csv), "--rates", str(rates_csv), "--output", str(output)])

    assert process.returncode == 2, process.stderr
    assert "GBP" in process.stderr
    assert "Traceback" not in process.stderr
    assert not output.exists()
