import pandas as pd

from services.numeric_utils import numeric_parse_ratio, parse_number, parse_numeric_series


def test_parse_number_handles_common_dirty_formats():
    assert parse_number("1,250.50") == 1250.5
    assert parse_number("18450 USD") == 18450
    assert parse_number("10%") == 10
    assert parse_number("۱۲۳۴") == 1234
    assert parse_number("(1,200)") == -1200
    assert parse_number("$2,000.00") == 2000


def test_parse_number_rejects_identifier_like_values():
    assert parse_number("ORD-14040001") is None
    assert parse_number("P-104") is None
    assert parse_number("N/A") is None
    assert parse_number("") is None


def test_parse_numeric_series_and_ratio():
    series = pd.Series(["1,000", "2 USD", "نامشخص", None])

    parsed = parse_numeric_series(series)

    assert parsed.tolist()[:2] == [1000.0, 2.0]
    assert pd.isna(parsed.iloc[2])
    assert 0.6 < numeric_parse_ratio(series) < 0.7
