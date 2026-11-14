"""Testes adicionais: aceitação com os arquivos reais do projeto."""

import json

from cli_support import DATA_DIR, run_cli_process


def test_validation_sample_matches_readme(tmp_path):
    """A amostra do README (CSV alinhado com espaços e nomes com vírgula entre aspas) gera as tabelas esperadas."""
    output = tmp_path / "exemplo.json"
    process = run_cli_process(
        [
            "--input", str(DATA_DIR / "exemplo-validacao.csv"),
            "--rates", str(DATA_DIR / "taxas_cambio.csv"),
            "--output", str(output),
        ]
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(output.read_text(encoding="utf-8"))

    assert report["summary"] == {
        "total_reservations": 12,
        "confirmed_reservations": 9,
        "cancelled_reservations": 2,
        "no_show_reservations": 1,
        "total_room_nights": 28,
        "total_amount_brl": "7566.00",
        "average_nightly_rate_brl": "270.21",
    }
    assert report["by_month"] == [
        {"month": "2025-01", "reservations": 8, "room_nights": 25, "total_brl": "6684.00"},
        {"month": "2025-02", "reservations": 1, "room_nights": 3, "total_brl": "882.00"},
    ]
    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel Aurora Paulista", "room_nights": 3, "total_brl": "1200.00"},
        {"hotel_id": "H02", "hotel_name": "Hotel Mirante", "room_nights": 2, "total_brl": "1084.00"},
        {"hotel_id": "H12", "hotel_name": "Hotel Miami Beach", "room_nights": 1, "total_brl": "1000.00"},
        {"hotel_id": "H10", "hotel_name": "Hotel Madrid, Gran Vía", "room_nights": 4, "total_brl": "900.00"},
        {"hotel_id": "H09", "hotel_name": "Hotel Lisboa, Centro", "room_nights": 3, "total_brl": "882.00"},
    ]


def test_official_command_on_full_dataset_is_consistent(tmp_path):
    """O comando do README processa o dataset completo e o relatório é internamente consistente."""
    reservations_csv = DATA_DIR / "reservas_hoteis.csv"
    output = tmp_path / "report.json"
    process = run_cli_process(
        ["--input", str(reservations_csv), "--rates", str(DATA_DIR / "taxas_cambio.csv"), "--output", str(output)]
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    summary = report["summary"]

    data_lines = [line for line in reservations_csv.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
    assert summary["total_reservations"] == len(data_lines)
    assert (
        summary["confirmed_reservations"] + summary["cancelled_reservations"] + summary["no_show_reservations"]
        == summary["total_reservations"]
    )
    assert sum(month["reservations"] for month in report["by_month"]) == summary["confirmed_reservations"]
    assert sum(month["room_nights"] for month in report["by_month"]) == summary["total_room_nights"]
    assert len(report["top_hotels"]) == 5
