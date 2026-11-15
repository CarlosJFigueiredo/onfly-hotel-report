"""Testes adicionais: agregação por mês e ranking de hotéis."""

from helpers import run_cli


def test_by_month_is_sorted_ascending_across_years(tmp_path):
    """`by_month` sai em ordem crescente de mês, inclusive na virada de ano, independente da ordem do arquivo."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "checkin_date": "2025-03-05", "checkout_date": "2025-03-06"},
            {"reservation_id": "R-2", "checkin_date": "2024-12-10", "checkout_date": "2024-12-11"},
            {"reservation_id": "R-3", "checkin_date": "2025-01-15", "checkout_date": "2025-01-16"},
        ],
    )
    assert [month["month"] for month in report["by_month"]] == ["2024-12", "2025-01", "2025-03"]


def test_whole_stay_counts_in_checkin_month_across_year_boundary(tmp_path):
    """Estadia que vira o ano conta inteira no mês do check-in, com noites = dias x quartos."""
    report = run_cli(
        tmp_path,
        [
            {
                "reservation_id": "R-1",
                "checkin_date": "2024-12-30",
                "checkout_date": "2025-01-02",
                "rooms": "2",
                "amount": "600.00",
            }
        ],
    )
    assert report["summary"]["total_room_nights"] == 6
    assert report["by_month"] == [{"month": "2024-12", "reservations": 1, "room_nights": 6, "total_brl": "600.00"}]


def test_cancelled_and_no_show_are_excluded_from_breakdowns(tmp_path):
    """CANCELLED e NO_SHOW não aparecem em `by_month` nem em `top_hotels`."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01", "status": "CONFIRMED", "amount": "100.00"},
            {
                "reservation_id": "R-2",
                "hotel_id": "H02",
                "status": "CANCELLED",
                "amount": "5000.00",
                "checkin_date": "2025-02-10",
                "checkout_date": "2025-02-12",
            },
            {
                "reservation_id": "R-3",
                "hotel_id": "H03",
                "status": "NO_SHOW",
                "amount": "3000.00",
                "checkin_date": "2025-03-10",
                "checkout_date": "2025-03-12",
            },
        ],
    )
    assert report["by_month"] == [{"month": "2025-01", "reservations": 1, "room_nights": 1, "total_brl": "100.00"}]
    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01"]


def test_top_hotels_aggregate_all_reservations_of_a_hotel(tmp_path):
    """O ranking soma noites e valores (em BRL) de todas as reservas confirmadas do hotel."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01", "hotel_name": "Hotel A", "amount": "100.00"},
            {
                "reservation_id": "R-2",
                "hotel_id": "H01",
                "hotel_name": "Hotel A",
                "currency": "USD",
                "amount": "10.00",
                "checkin_date": "2025-02-01",
                "checkout_date": "2025-02-03",
            },
            {"reservation_id": "R-3", "hotel_id": "H02", "hotel_name": "Hotel B", "amount": "150.00"},
        ],
    )
    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel A", "room_nights": 3, "total_brl": "154.20"},
        {"hotel_id": "H02", "hotel_name": "Hotel B", "room_nights": 1, "total_brl": "150.00"},
    ]


def test_top_hotels_tie_is_broken_by_hotel_id_before_truncating(tmp_path):
    """Com `total_brl` empatado, vence o menor `hotel_id`; o corte de `--top` acontece depois da ordenação."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H03", "amount": "100.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "amount": "100.00"},
            {"reservation_id": "R-3", "hotel_id": "H02", "amount": "100.00"},
        ],
        top=2,
    )
    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01", "H02"]


def test_all_rows_are_read_regardless_of_file_size(tmp_path):
    """Não há limite de linhas: todas as reservas do arquivo entram no relatório."""
    rows = [{"reservation_id": f"R-{index}", "amount": "100.00"} for index in range(1, 501)]
    report = run_cli(tmp_path, rows)
    assert report["summary"]["total_reservations"] == 500
    assert report["summary"]["total_room_nights"] == 500
    assert report["summary"]["total_amount_brl"] == "50000.00"
