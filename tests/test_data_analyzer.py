import pandas as pd

from services.data_analyzer import analyze_dataset


def test_analyze_dataset():

    data = pd.DataFrame({
        "Name": [
            "Ali",
            "Sara",
            "Ali"
        ],
        "Age": [
            20,
            25,
            20
        ]
    })

    result = analyze_dataset(data)

    assert result["rows"] == 3
    assert result["columns"] == 2
    assert result["duplicate_rows"] == 1


def test_detect_missing_values():

    data = pd.DataFrame({
        "Name": [
            "Ali",
            None,
            "Reza"
        ],
        "Age": [
            20,
            25,
            None
        ]
    })

    result = analyze_dataset(data)

    assert result["total_missing"] == 2


def test_detect_numeric_columns():

    data = pd.DataFrame({
        "Name": [
            "Ali",
            "Sara"
        ],
        "Age": [
            20,
            25
        ]
    })

    result = analyze_dataset(data)

    assert "Age" in result["numeric_columns"]
    assert "Name" in result["text_columns"]


def test_assess_quality_scores_and_lists_issues(messy_sales):
    from services.data_cleaner import clean_dataset
    from services.data_analyzer import assess_quality

    cleaning = clean_dataset(messy_sales)
    quality = assess_quality(messy_sales, cleaning.data, cleaning)

    assert 0 <= quality["score"] <= 100
    assert quality["duplicate_rows"] == 1
    assert quality["high_severity"] >= 1
    assert all({"ستون", "نوع مشکل", "شدت", "توضیح"} <= set(issue) for issue in quality["issues"])


def test_assess_quality_gives_clean_data_a_high_score():
    from services.data_analyzer import assess_quality

    clean = pd.DataFrame({"Amount": [10.0, 20.0, 30.0], "Region": ["A", "B", "A"]})

    quality = assess_quality(clean, clean)

    assert quality["score"] >= 95
    assert quality["total_missing"] == 0


def test_analyze_dataset_classifies_columns():
    from services.data_analyzer import analyze_dataset

    data = pd.DataFrame(
        {
            "Order_Date": pd.to_datetime(["2026-01-01", "2026-02-01"]),
            "Amount": [1.0, 2.0],
            "Region": ["A", "B"],
        }
    )

    structure = analyze_dataset(data)

    assert structure["date_columns"] == ["Order_Date"]
    assert "Amount" in structure["numeric_columns"]
    assert "Region" in structure["text_columns"]
