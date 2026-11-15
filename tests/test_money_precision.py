"""Testes adicionais: exatidão monetária (Decimal, soma exata, arredondamento half-up na serialização)."""

from helpers import run_cli


def test_converted_amount_is_rounded_half_up_without_float_error(tmp_path):
    """0.75 USD x 5.42 = 4.065 exatos -> "4.07".

    Arredondamento bancário (half-even) ou conversão via float produzem "4.06".
    """
    report = run_cli(tmp_path, [{"reservation_id": "R-1", "currency": "USD", "amount": "0.75"}])
    assert report["summary"]["total_amount_brl"] == "4.07"


def test_amounts_are_summed_exactly_before_rounding(tmp_path):
    """6.504 + 9.214 = 15.718 -> "15.72"; arredondar cada reserva antes de somar daria "15.71"."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "currency": "USD", "amount": "1.20"},
            {"reservation_id": "R-2", "currency": "USD", "amount": "1.70"},
        ],
    )
    assert report["summary"]["total_amount_brl"] == "15.72"
    assert report["by_month"][0]["total_brl"] == "15.72"
    assert report["top_hotels"][0]["total_brl"] == "15.72"


def test_average_nightly_rate_is_rounded_half_up(tmp_path):
    """10.05 / 2 noites = 5.025 -> "5.03" (half-even daria "5.02")."""
    report = run_cli(
        tmp_path,
        [{"reservation_id": "R-1", "amount": "10.05", "checkin_date": "2025-01-10", "checkout_date": "2025-01-12"}],
    )
    assert report["summary"]["average_nightly_rate_brl"] == "5.03"


def test_report_without_billable_reservations_has_zero_totals(tmp_path):
    """Sem CONFIRMED não há divisão por zero: totais e média "0.00", listas vazias, contagens preservadas."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "status": "CANCELLED"},
            {"reservation_id": "R-2", "status": "NO_SHOW"},
        ],
    )
    assert report["summary"] == {
        "total_reservations": 2,
        "confirmed_reservations": 0,
        "cancelled_reservations": 1,
        "no_show_reservations": 1,
        "total_room_nights": 0,
        "total_amount_brl": "0.00",
        "average_nightly_rate_brl": "0.00",
    }
    assert report["by_month"] == []
    assert report["top_hotels"] == []
