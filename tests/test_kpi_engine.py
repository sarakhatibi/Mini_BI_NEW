import pandas as pd

from services.data_cleaner import clean_dataset
from services.kpi_engine import calculate_kpis
from services.semantic_profiler import profile_dataset


def _kpis(df):
    cleaned = clean_dataset(df).data
    return cleaned, calculate_kpis(cleaned, profile_dataset(cleaned))


def test_net_sales_excludes_cancelled_orders(messy_sales):
    _, result = _kpis(messy_sales)

    # 12,505 + 60,000 (pending) + 60,000 (completed); the cancelled 16,000 is out.
    assert result.get("total_sales").value == 132505
    assert result.get("cancelled_value").value == 16000


def test_cancellation_rate_and_receivables(messy_sales):
    _, result = _kpis(messy_sales)

    assert round(result.get("cancellation_rate").value, 1) == 25.0
    assert result.get("pending_amount").value == 60000


def test_best_dimensions_use_readable_labels(messy_sales):
    _, result = _kpis(messy_sales)

    assert result.get("best_product").display == "فروسیلیس"
    assert result.get("best_customer").display in {"فولاد جنوب", "پارس صنعت"}


def test_order_count_uses_unique_identifier(messy_sales):
    _, result = _kpis(messy_sales)

    assert result.get("order_count").value == 4
    assert result.get("total_rows").value == 4


def test_kpis_on_empty_dataframe():
    result = calculate_kpis(pd.DataFrame())

    assert result.kpis == []
    assert result.as_dict() == {}


def test_kpis_fall_back_to_generic_measure():
    data = pd.DataFrame({"alpha": [1.0, 2.0, 3.0], "beta": ["x", "y", "x"]})

    result = calculate_kpis(data)

    assert result.get("primary_measure_total").value == 6
    assert result.get("total_sales") is None


def test_quantity_kpi_skipped_for_mixed_units():
    data = pd.DataFrame(
        {
            "Quantity": [1, 2, 3],
            "Unit": ["kg", "ton", "kg"],
            "Total_Amount_USD": [10.0, 20.0, 30.0],
        }
    )

    result = calculate_kpis(data)

    assert result.get("total_quantity") is None
    assert result.context["quantity_units"] == 2


def test_monthly_growth_ignores_incomplete_last_month():
    data = pd.DataFrame(
        {
            "Order_Date": pd.to_datetime(
                ["2026-01-15", "2026-02-15", "2026-03-15", "2026-04-01"]
            ),
            "Total_Amount_USD": [100.0, 200.0, 300.0, 5.0],
        }
    )

    result = calculate_kpis(data)

    assert result.context["partial_last_month"] is True
    assert round(result.get("mom_growth").value, 1) == 50.0
