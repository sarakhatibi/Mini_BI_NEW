import pandas as pd

from services.data_cleaner import clean_dataset
from services.semantic_profiler import profile_dataset


def test_profile_detects_business_roles(messy_sales):
    profile = profile_dataset(clean_dataset(messy_sales).data)

    assert profile.money_column == "Total_Amount_USD"
    assert profile.quantity_column == "Quantity"
    assert profile.primary_date == "Order_Date"
    assert profile.customer_column == "Customer"
    assert profile.region_column == "Province"
    assert profile.status_column == "Status"
    assert profile.order_id_column == "Order_ID"


def test_profile_prefers_readable_product_over_code(messy_sales):
    profile = profile_dataset(clean_dataset(messy_sales).data)

    assert profile.product_column == "Product"
    assert "Product_Code" in profile.identifier_columns + profile.category_columns


def test_profile_detects_status_groups(messy_sales):
    profile = profile_dataset(clean_dataset(messy_sales).data)

    assert "لغو شده" in profile.negative_statuses
    assert "در انتظار پرداخت" in profile.pending_statuses


def test_profile_marks_percent_columns(messy_sales):
    profile = profile_dataset(clean_dataset(messy_sales).data)

    assert "Discount_Pct" in profile.percent_columns
    assert "Tax_Pct" in profile.percent_columns
    assert "Discount_Pct" not in profile.measure_columns


def test_profile_of_unknown_dataset_still_works():
    data = pd.DataFrame({"alpha": [1, 2, 3], "beta": ["x", "y", "x"]})

    profile = profile_dataset(data)

    assert profile.primary_measure == "alpha"
    assert "beta" in profile.category_columns
