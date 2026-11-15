"""Testes adicionais: leitura dos CSVs de reservas e de câmbio pelos repositórios."""

from decimal import Decimal

import pytest
from cli_support import DATA_DIR

from onfly_report.exceptions import InputFileError
from onfly_report.repositories.csv_rate_repository import CsvRateRepository
from onfly_report.repositories.csv_reservation_repository import REQUIRED_COLUMNS, CsvReservationRepository


def test_reservation_repository_reads_every_row_aligned():
    """As 300 reservas são lidas com as 15 colunas no lugar, inclusive nomes com vírgula entre aspas."""
    rows = CsvReservationRepository(DATA_DIR / "reservas_hoteis.csv").read()

    assert [row.line_number for row in rows] == list(range(2, 302))
    for row in rows:
        assert set(row.values) == set(REQUIRED_COLUMNS), row.line_number
        assert None not in row.values.values(), row.line_number
    hotel_names = {row.values["hotel_name"].strip() for row in rows}
    assert {"Hotel Lisboa, Centro", "Hotel Madrid, Gran Vía"} <= hotel_names


def test_rate_repository_reads_rates_table():
    rates = CsvRateRepository(DATA_DIR / "taxas_cambio.csv").read()
    assert rates == {"BRL": Decimal("1"), "USD": Decimal("5.42"), "EUR": Decimal("5.88")}


def test_rate_repository_accepts_same_layout_as_reservations(tmp_path):
    """A tabela de câmbio aceita o formato alinhado por espaços e normaliza a moeda para maiúsculas."""
    path = tmp_path / "rates.csv"
    path.write_text("currency , rate_to_brl\nusd      , 5.420000\n BRL     , 1.000000\n", encoding="utf-8")
    assert CsvRateRepository(path).read() == {"USD": Decimal("5.42"), "BRL": Decimal("1")}


@pytest.mark.parametrize(
    ("content", "message"),
    [
        pytest.param("currency,rate_to_brl\n", "vazia", id="sem_linhas"),
        pytest.param("currency,rate_to_brl\nUSD,\n", "incompleta", id="taxa_em_branco"),
        pytest.param("currency,rate_to_brl\nUSD,abc\n", "inválida", id="taxa_nao_numerica"),
        pytest.param("currency,rate\nUSD,5.42\n", "ausentes", id="coluna_ausente"),
    ],
)
def test_rate_repository_rejects_invalid_table(tmp_path, content, message):
    path = tmp_path / "rates.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(InputFileError, match=message):
        CsvRateRepository(path).read()
