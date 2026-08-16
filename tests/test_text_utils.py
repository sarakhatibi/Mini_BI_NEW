from services.text_utils import normalize_column_name, normalize_text, slugify_column_name, to_ascii_digits


def test_to_ascii_digits():
    assert to_ascii_digits("۱۴۰۵/۰۲/۳۱") == "1405/02/31"
    assert to_ascii_digits("١٢٣") == "123"


def test_normalize_text_unifies_persian_variants():
    assert normalize_text("پارس‌ صنعت") == normalize_text("پارس صنعت ")
    assert normalize_text("كيفيت") == "کیفیت"
    assert normalize_text("  چند   فاصله ") == "چند فاصله"


def test_column_name_helpers():
    assert normalize_column_name("  Total  Amount USD ") == "Total Amount USD"
    assert slugify_column_name("Total_Amount_USD") == "total_amount_usd"
    assert slugify_column_name("Total Amount (USD)") == "total_amount_usd"
