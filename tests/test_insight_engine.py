
import pandas as pd

from services.kpi_engine import calculate_kpis
from services.insight_engine import generate_insights


def test_generate_insights():

    data = pd.DataFrame({
        "Quantity": [2, 3, 5],
        "Total_Amount_USD": [
            20,
            30,
            50
        ]
    })

    kpis = calculate_kpis(data)

    insights = generate_insights(
        data,
        kpis
    )

    assert len(insights) > 0

    assert any(
        "Total sales" in insight
        for insight in insights
    )


def test_generate_insights_with_empty_data():

    data = pd.DataFrame()

    insights = generate_insights(
        data,
        {}
    )

    assert insights == []

def test_generate_insights_with_empty_dataframe():

    data = pd.DataFrame()

    result = generate_insights(
        data,
        {}
    )

    assert result == []


def test_generate_insights_with_invalid_sales_values():

    data = pd.DataFrame({
        "Customer": [
            "Ali",
            "Sara",
            "Reza"
        ],
        "Category": [
            "A",
            "B",
            "A"
        ],
        "Total_Amount_USD": [
            100,
            "N/A",
            300
        ]
    })

    kpis = {
        "total_sales": 400,
        "sales_column": "Total_Amount_USD"
    }

    result = generate_insights(
        data,
        kpis
    )

    assert any(
        "Total sales are $400.00"
        in insight
        for insight in result
    )

    assert any(
        "highest individual transaction"
        in insight
        for insight in result
    )

    assert any(
        "highest-value customer"
        in insight
        for insight in result
    )


def test_generate_insights_with_missing_kpis():

    data = pd.DataFrame({
        "Total_Amount_USD": [
            100,
            200,
            300
        ]
    })

    result = generate_insights(
        data,
        {}
    )

    assert any(
        "current analysis is based on 3 records"
        in insight
        for insight in result
    )


def test_generate_insights_with_none_kpis():

    data = pd.DataFrame({
        "Total_Amount_USD": [
            100,
            200
        ]
    })

    result = generate_insights(
        data,
        None
    )

    assert any(
        "current analysis is based on 2 records"
        in insight
        for insight in result
    )