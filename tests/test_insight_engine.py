import pandas as pd

from services.insight_engine import generate_insights
from services.pipeline import build_analysis


def _texts(insights):
    return " ".join(insight.text for insight in insights)


def test_insights_cover_sales_and_risks(messy_sales):
    bundle = build_analysis(messy_sales)

    insights = generate_insights(bundle.data, profile=bundle.profile)

    text = _texts(insights)
    assert "فروش خالص" in text
    assert "لغو" in text
    assert "وصول نشده" in text
    assert all(insight.level in {"info", "warning", "positive"} for insight in insights)


def test_insights_mention_record_count(messy_sales):
    bundle = build_analysis(messy_sales)

    insights = generate_insights(bundle.data, profile=bundle.profile)

    assert f"{len(bundle.data):,} رکورد" in _texts(insights)


def test_insights_with_empty_dataframe():
    assert generate_insights(pd.DataFrame()) == []


def test_insights_without_business_columns():
    data = pd.DataFrame({"alpha": [1, 2, 3]})

    insights = generate_insights(data)

    assert len(insights) >= 1
    assert "3 رکورد" in _texts(insights)
