"""Testes adicionais: códigos de saída (0 sucesso, 2 entrada/argumento inválido, 1 erro inesperado)."""

import pytest
from cli_support import run_cli_process, write_rates, write_reservations
from helpers import COLUMNS

from onfly_report import cli


@pytest.mark.parametrize(
    "build_args",
    [
        pytest.param(lambda i, r, o: ["--input", i, "--rates", r, "--output", o, "--top", "0"], id="top_zero"),
        pytest.param(lambda i, r, o: ["--input", i, "--rates", r, "--output", o, "--top", "abc"], id="top_nao_inteiro"),
        pytest.param(lambda i, r, o: ["--rates", r, "--output", o], id="sem_input"),
        pytest.param(lambda i, r, o: ["--input", i, "--output", o], id="sem_rates"),
    ],
)
def test_invalid_arguments_exit_with_code_2(tmp_path, build_args):
    input_csv = write_reservations(tmp_path / "reservas.csv", [{}])
    rates_csv = write_rates(tmp_path / "rates.csv")
    output = tmp_path / "report.json"

    process = run_cli_process(build_args(str(input_csv), str(rates_csv), str(output)))

    assert process.returncode == 2
    assert not output.exists()


def _missing_reservations_file(tmp_path):
    return tmp_path / "nao_existe.csv", write_rates(tmp_path / "rates.csv")


def _missing_rates_file(tmp_path):
    return write_reservations(tmp_path / "reservas.csv", [{}]), tmp_path / "nao_existe.csv"


def _missing_required_column(tmp_path):
    columns = [column for column in COLUMNS if column != "amount"]
    return write_reservations(tmp_path / "reservas.csv", [{}], columns=columns), write_rates(tmp_path / "rates.csv")


def _invalid_date_in_cancelled_row(tmp_path):
    rows = [{"reservation_id": "R-1"}, {"reservation_id": "R-2", "status": "CANCELLED", "checkin_date": "2025-02-30"}]
    return write_reservations(tmp_path / "reservas.csv", rows), write_rates(tmp_path / "rates.csv")


def _non_numeric_amount(tmp_path):
    rows = [{"reservation_id": "R-1", "amount": "cem reais"}]
    return write_reservations(tmp_path / "reservas.csv", rows), write_rates(tmp_path / "rates.csv")


def _non_positive_rate(tmp_path):
    rates = write_rates(tmp_path / "rates.csv", "currency,rate_to_brl\nBRL,0\n")
    return write_reservations(tmp_path / "reservas.csv", [{}]), rates


@pytest.mark.parametrize(
    "prepare",
    [
        pytest.param(_missing_reservations_file, id="reservas_inexistente"),
        pytest.param(_missing_rates_file, id="cambio_inexistente"),
        pytest.param(_missing_required_column, id="coluna_obrigatoria_ausente"),
        # A conversão de tipos vem antes do filtro por status: linha inválida não é descartada.
        pytest.param(_invalid_date_in_cancelled_row, id="data_invalida_em_reserva_cancelada"),
        pytest.param(_non_numeric_amount, id="valor_nao_numerico"),
        pytest.param(_non_positive_rate, id="taxa_nao_positiva"),
    ],
)
def test_invalid_input_exits_with_code_2_without_writing_report(tmp_path, prepare):
    input_csv, rates_csv = prepare(tmp_path)
    output = tmp_path / "report.json"

    process = run_cli_process(["--input", str(input_csv), "--rates", str(rates_csv), "--output", str(output)])

    assert process.returncode == 2, process.stderr
    assert not output.exists()
    assert "Traceback" not in process.stderr


@pytest.mark.parametrize(
    ("column", "value"),
    [
        pytest.param("amount", "cem reais", id="valor"),
        pytest.param("rooms", "dois", id="quartos"),
        pytest.param("checkin_date", "2025-02-30", id="data"),
    ],
)
def test_invalid_value_message_points_to_line_and_column(tmp_path, column, value):
    """A mensagem de valor inválido indica a linha física, a coluna e o valor recebido."""
    input_csv = write_reservations(tmp_path / "reservas.csv", [{"reservation_id": "R-1"}, {column: value}])
    rates_csv = write_rates(tmp_path / "rates.csv")
    output = tmp_path / "report.json"

    process = run_cli_process(["--input", str(input_csv), "--rates", str(rates_csv), "--output", str(output)])

    assert process.returncode == 2, process.stderr
    assert f"linha 3: valor inválido em {column}: '{value}'" in process.stderr


def test_unwritable_output_exits_with_code_1_and_clear_message(tmp_path):
    """Falha ao gravar o relatório (aqui, `--output` é um diretório) devolve 1 com mensagem, sem traceback."""
    input_csv = write_reservations(tmp_path / "reservas.csv", [{}])
    rates_csv = write_rates(tmp_path / "rates.csv")
    output_dir = tmp_path / "saida"
    output_dir.mkdir()

    process = run_cli_process(["--input", str(input_csv), "--rates", str(rates_csv), "--output", str(output_dir)])

    assert process.returncode == 1
    assert "não foi possível gravar o relatório" in process.stderr
    assert "Traceback" not in process.stderr


def test_unexpected_error_exits_with_code_1(tmp_path, monkeypatch, caplog):
    """Falha não prevista na geração do relatório devolve 1, registra o erro e não grava saída."""

    def fail(self):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(cli.ReportBuilder, "build", fail)
    input_csv = write_reservations(tmp_path / "reservas.csv", [{}])
    rates_csv = write_rates(tmp_path / "rates.csv")
    output = tmp_path / "report.json"

    exit_code = cli.main(["--input", str(input_csv), "--rates", str(rates_csv), "--output", str(output)])

    assert exit_code == 1
    assert not output.exists()
    assert "erro inesperado" in caplog.text
