import pandas as pd

from services.kpi_engine import calculate_kpis


def test_calculate_kpis():

    data = pd.DataFrame({
        "Quantity": [2, 3, 5],
        "Total_Amount_USD": [20, 30, 50]
    })

    result = calculate_kpis(data)

    assert result["total_rows"] == 3
    assert result["total_quantity"] == 10
    assert result["total_sales"] == 100
    assert result["average_order_value"] == 100 / 3


def test_calculate_kpis_with_alternative_names():

    data = pd.DataFrame({
        "Qty": [2, 3, 5],
        "Revenue": [20, 30, 50]
    })

    result = calculate_kpis(data)

    assert result["total_rows"] == 3
    assert result["total_quantity"] == 10
    assert result["total_sales"] == 100


def test_calculate_kpis_without_sales():

    data = pd.DataFrame({
        "Quantity": [2, 3, 5]
    })

    result = calculate_kpis(data)

    assert result["total_rows"] == 3
    assert result["total_quantity"] == 10
    assert "total_sales" not in result

def test_calculate_kpis_with_invalid_numeric_values():

    data = pd.DataFrame({
        "Quantity": [
            2,
            3,
            "N/A",
            5
        ],
        "Total_Amount_USD": [
            20,
            30,
            "unknown",
            50
        ]
    })

    result = calculate_kpis(data)

    assert result["total_rows"] == 4
    assert result["total_quantity"] == 10
    assert result["total_sales"] == 100


def test_calculate_kpis_with_empty_dataframe():

    data = pd.DataFrame()

    result = calculate_kpis(data)

    assert result["total_rows"] == 0
def test_calculate_kpis_with_customers():

    data = pd.DataFrame({
        "Customer": [
            "Ali",
            "Sara",
            "Ali",
            "Reza"
        ]
    })

    result = calculate_kpis(data)

    assert result["total_rows"] == 4
    assert result["unique_customers"] == 3