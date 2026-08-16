import pandas as pd

from services.chart_engine import create_charts


def test_create_charts_with_numeric_and_text_data():

    data = pd.DataFrame({
        "Region": [
            "East",
            "West",
            "East",
            "North"
        ],
        "Sales": [
            100,
            200,
            150,
            300
        ]
    })

    charts = create_charts(data)

    assert len(charts) >= 2


def test_create_charts_with_empty_dataframe():

    data = pd.DataFrame()

    charts = create_charts(data)

    assert charts == []


def test_create_charts_with_only_text():

    data = pd.DataFrame({
        "Name": [
            "Ali",
            "Sara",
            "Reza"
        ]
    })

    charts = create_charts(data)

    assert charts == []


def test_create_scatter_with_two_numeric_columns():

    data = pd.DataFrame({
        "Quantity": [1, 2, 3, 4],
        "Sales": [10, 20, 30, 40]
    })

    charts = create_charts(data)

    assert len(charts) >= 2