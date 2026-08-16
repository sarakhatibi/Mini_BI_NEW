"""Numeric parsing helpers for values stored as free-form text."""

import re

import pandas as pd

from services.text_utils import to_ascii_digits

_THOUSANDS_GROUPED = re.compile(r"^\d{1,3}(,\d{3})+(\.\d+)?$")
_EUROPEAN_GROUPED = re.compile(r"^[-+]?\d{1,3}(\.\d{3})+(,\d+)?$")
_NUMBER_TOKEN = re.compile(r"[-+]?\d*\.?\d+")
_PERCENT_MARKS = ("%", "٪")
# Only currency symbols or space separated unit/currency words may surround a
# number. Codes such as "ORD-14040001" must stay text.
_ALLOWED_PREFIX = re.compile(r"^[\s$€£¥﷼+]*$")
_ALLOWED_SUFFIX = re.compile(r"^[\s$€£¥﷼]*(\s[^\d\s]{1,12}\.?)?\s*$")


def parse_number(value):
    """Parse a single messy value into a float, or return None.

    Handles thousand separators, currency symbols and codes, unit suffixes,
    percent signs, Persian digits and accounting style negatives.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return None if pd.isna(value) else float(value)

    text = to_ascii_digits(str(value)).strip()
    if text == "" or text.lower() in {"nan", "none", "null", "-", "n/a", "na"}:
        return None

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    for mark in _PERCENT_MARKS:
        text = text.replace(mark, "")

    text = text.replace("٬", ",").replace("،", ",").replace("\u00a0", " ")

    if _EUROPEAN_GROUPED.match(text.replace(" ", "")):
        text = text.replace(".", "").replace(",", ".")
    elif _THOUSANDS_GROUPED.match(text.replace(" ", "")):
        text = text.replace(",", "")
    elif "," in text and "." not in text and re.fullmatch(r"[-+]?\d+,\d+", text):
        # Decimal comma, e.g. "1234,56".
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")

    # Accept currency symbols and space separated unit/currency words only.
    match = _NUMBER_TOKEN.search(text)
    if match is None:
        return None

    prefix = text[: match.start()]
    suffix = text[match.end():]
    if not _ALLOWED_PREFIX.match(prefix) or not _ALLOWED_SUFFIX.match(suffix):
        return None

    try:
        number = float(match.group())
    except ValueError:
        return None

    return -number if negative else number


def parse_numeric_series(series: pd.Series) -> pd.Series:
    """Vectorised wrapper around :func:`parse_number`."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype("float64")
    return series.map(parse_number).astype("float64")


def numeric_parse_ratio(series: pd.Series) -> float:
    """Share of non-empty values that can be interpreted as numbers."""
    non_empty = series.dropna()
    non_empty = non_empty[non_empty.astype(str).str.strip() != ""]
    if non_empty.empty:
        return 0.0
    return float(parse_numeric_series(non_empty).notna().mean())
