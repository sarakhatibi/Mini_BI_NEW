"""Text normalization helpers for Persian/Arabic and mixed-format datasets."""

import re
import unicodedata

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

_DIGIT_TABLE = {
    ord(persian): ascii_digit
    for persian, ascii_digit in zip(PERSIAN_DIGITS, ASCII_DIGITS)
}
_DIGIT_TABLE.update(
    {
        ord(arabic): ascii_digit
        for arabic, ascii_digit in zip(ARABIC_DIGITS, ASCII_DIGITS)
    }
)

# Arabic letters that have a Persian equivalent, plus invisible characters.
_LETTER_TABLE = {
    ord("ي"): "ی",
    ord("ى"): "ی",
    ord("ك"): "ک",
    ord("ۀ"): "ه",
    ord("ة"): "ه",
    ord("\u200c"): " ",  # zero width non-joiner
    ord("\u200f"): "",   # right-to-left mark
    ord("\u200e"): "",   # left-to-right mark
    ord("\ufeff"): "",   # byte order mark
}

_ARABIC_DIACRITICS = re.compile(r"[\u064b-\u0652\u0670]")
_WHITESPACE = re.compile(r"\s+")


def to_ascii_digits(value: str) -> str:
    """Convert Persian/Arabic-Indic digits to ASCII digits."""
    return value.translate(_DIGIT_TABLE)


def normalize_text(value: str) -> str:
    """Normalize a text value so equivalent labels compare equal.

    Applies Unicode NFKC, unifies Arabic/Persian letter variants, removes
    diacritics and invisible marks, converts digits to ASCII and collapses
    whitespace.
    """
    text = unicodedata.normalize("NFKC", str(value))
    text = text.translate(_LETTER_TABLE)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = to_ascii_digits(text)
    return _WHITESPACE.sub(" ", text).strip()


def normalize_column_name(value: str) -> str:
    """Normalize a column header while keeping it human readable."""
    text = normalize_text(value)
    text = text.replace("\n", " ")
    return _WHITESPACE.sub(" ", text).strip()


def slugify_column_name(value: str) -> str:
    """Lower-cased, underscore separated key used for name-based matching."""
    text = normalize_column_name(value).lower()
    text = re.sub(r"[^0-9a-z\u0600-\u06ff]+", "_", text)
    return text.strip("_")
