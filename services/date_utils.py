"""Date parsing helpers, including Jalali (Solar Hijri) support."""

import re
from datetime import date

import pandas as pd

from services.text_utils import to_ascii_digits

_JALALI_PATTERN = re.compile(r"^(1[2-5]\d{2})[/\-.](\d{1,2})[/\-.](\d{1,2})$")

_GREGORIAN_MONTH_DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _is_gregorian_leap(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> date:
    """Convert a Jalali (Solar Hijri) date to a Gregorian date."""
    if not 1 <= jm <= 12:
        raise ValueError(f"Invalid Jalali month: {jm}")

    jy += 1595
    days = (
        -355668
        + (365 * jy)
        + ((jy // 33) * 8)
        + (((jy % 33) + 3) // 4)
        + jd
        + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
    )

    gy = 400 * (days // 146097)
    days %= 146097

    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1

    gy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365

    gd = days + 1
    month_days = list(_GREGORIAN_MONTH_DAYS)
    if _is_gregorian_leap(gy):
        month_days[2] = 29

    gm = 12
    for month in range(1, 13):
        if gd <= month_days[month]:
            gm = month
            break
        gd -= month_days[month]

    return date(gy, gm, gd)


def parse_jalali_value(value) -> pd.Timestamp:
    """Parse a single Jalali date string, returning NaT when not applicable."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT

    text = to_ascii_digits(str(value)).strip()
    match = _JALALI_PATTERN.match(text)
    if match is None:
        return pd.NaT

    year, month, day = (int(part) for part in match.groups())
    try:
        return pd.Timestamp(jalali_to_gregorian(year, month, day))
    except ValueError:
        # Out-of-range days such as 1405/02/31 in a 30-day month.
        return pd.NaT


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse a Series into datetimes, falling back to Jalali dates.

    Values that cannot be interpreted become NaT so the caller can report
    them instead of silently accepting a wrong date.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    text = series.astype(str).map(to_ascii_digits).str.strip()
    text = text.replace({"": None, "nan": None, "None": None, "NaT": None})

    parsed = pd.to_datetime(text, errors="coerce", format="mixed", dayfirst=False)

    unparsed = parsed.isna() & text.notna()
    if unparsed.any():
        jalali = text[unparsed].map(parse_jalali_value)
        parsed.loc[unparsed] = jalali

    return parsed
