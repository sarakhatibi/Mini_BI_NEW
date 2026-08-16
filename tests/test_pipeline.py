import pandas as pd
import pytest

from services.pipeline import build_analysis


def test_pipeline_reports_structure_and_quality(messy_sales):
    bundle = build_analysis(messy_sales)

    assert bundle.structure["rows"] == len(bundle.data)
    assert bundle.structure["columns"] == len(bundle.data.columns)
    assert 0 <= bundle.quality["score"] <= 100
    assert bundle.quality["duplicate_rows"] == 1


def test_pipeline_flags_duplicate_identifier(messy_sales):
    bundle = build_analysis(messy_sales)

    problems = {issue["نوع مشکل"] for issue in bundle.quality["issues"]}
    assert "رکورد تکراری" in problems


def test_pipeline_keeps_raw_data_untouched(messy_sales):
    original = messy_sales.copy()

    bundle = build_analysis(messy_sales)

    pd.testing.assert_frame_equal(messy_sales, original)
    assert len(bundle.raw_data) == len(original)


def test_pipeline_rejects_empty_dataframe():
    with pytest.raises(ValueError):
        build_analysis(pd.DataFrame())
