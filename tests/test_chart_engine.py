import pandas as pd

from services.chart_engine import create_charts
from services.pipeline import build_analysis


def test_charts_are_selected_from_the_profile(messy_sales):
    bundle = build_analysis(messy_sales)

    charts = create_charts(bundle.data, bundle.profile)

    keys = {chart.key for chart in charts}
    assert "trend" in keys
    assert any(key.startswith("top_") for key in keys)
    assert all(chart.figure is not None for chart in charts)


def test_charts_with_empty_dataframe():
    assert create_charts(pd.DataFrame()) == []


def test_charts_without_measures_still_summarise_categories():
    data = pd.DataFrame({"Name": ["Ali", "Sara", "Reza", "Ali"]})

    charts = create_charts(data)

    assert all(chart.title for chart in charts)


def test_charts_for_simple_numeric_dataset():
    data = pd.DataFrame({"Region": ["East", "West", "East", "North"], "Sales": [100, 200, 150, 300]})

    charts = create_charts(data)

    assert len(charts) >= 1
