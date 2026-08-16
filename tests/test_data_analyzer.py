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