import pandas as pd

from services.date_utils import jalali_to_gregorian, parse_dates, parse_jalali_value


def test_jalali_to_gregorian_known_dates():
    assert jalali_to_gregorian(1404, 1, 1).isoformat() == "2025-03-21"
    assert jalali_to_gregorian(1405, 2, 31).isoformat() == "2026-05-21"


def test_parse_jalali_value_accepts_persian_digits():
    assert parse_jalali_value("۱۴۰۵/۰۲/۳۱") == pd.Timestamp("2026-05-21")
    assert pd.isna(parse_jalali_value("not a date"))


def test_parse_dates_mixes_gregorian_and_jalali():
    parsed = parse_dates(pd.Series(["2026-01-10", "1405/02/31", "invalid"]))

    assert parsed.iloc[0] == pd.Timestamp("2026-01-10")
    assert parsed.iloc[1] == pd.Timestamp("2026-05-21")
    assert pd.isna(parsed.iloc[2])
