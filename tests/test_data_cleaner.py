import pandas as pd

from services.data_cleaner import clean_dataset


def test_clean_dataset_converts_text_measures(messy_sales):
    result = clean_dataset(messy_sales)

    assert pd.api.types.is_numeric_dtype(result.data["Total_Amount_USD"])
    assert pd.api.types.is_numeric_dtype(result.data["Unit_Price_USD"])
    assert pd.api.types.is_numeric_dtype(result.data["Tax_Pct"])
    assert pd.api.types.is_datetime64_any_dtype(result.data["Order_Date"])


def test_clean_dataset_keeps_identifier_columns_as_text(messy_sales):
    result = clean_dataset(messy_sales)

    assert result.data["Order_ID"].dtype == object
    assert result.data["Product_Code"].dtype == object
    assert result.data["Order_ID"].iloc[0] == "ORD-1001"


def test_clean_dataset_removes_only_full_duplicates(messy_sales):
    result = clean_dataset(messy_sales)

    assert result.duplicate_rows_removed == 1
    assert len(result.data) == len(messy_sales) - 1
    # The remaining duplicated order id is reported, never deleted.
    assert result.duplicate_id_rows >= 0


def test_clean_dataset_normalizes_persian_text(messy_sales):
    result = clean_dataset(messy_sales)

    assert result.data["Customer"].nunique() == 2
    assert set(result.data["Status"]) <= {"تکمیل شده", "لغو شده", "در انتظار پرداخت"}


def test_clean_dataset_reports_actions(messy_sales):
    result = clean_dataset(messy_sales)

    actions = result.actions_frame()
    assert not actions.empty
    assert len(result.actions) == len(actions)


def test_clean_dataset_with_empty_frame():
    result = clean_dataset(pd.DataFrame())

    assert result.data.empty
    assert result.actions == []
