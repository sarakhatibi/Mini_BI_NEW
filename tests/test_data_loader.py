import pandas as pd
import pytest

from services.data_loader import list_sheets, load_file


def test_load_csv(tmp_path):

    file_path = tmp_path / "sample.csv"

    data = pd.DataFrame({
        "Name": ["Ali", "Sara"],
        "Age": [20, 25]
    })

    data.to_csv(
        file_path,
        index=False
    )

    with open(
        file_path,
        "rb"
    ) as file:

        loaded = load_file(file)

    assert len(loaded) == 2
    assert list(loaded.columns) == [
        "Name",
        "Age"
    ]


def test_load_csv_with_semicolon_and_persian_text(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("نام;مبلغ\nعلی;1,000\nسارا;2,000\n", encoding="utf-8")

    with open(file_path, "rb") as file:
        loaded = load_file(file)

    assert list(loaded.columns) == ["نام", "مبلغ"]
    assert len(loaded) == 2


def test_load_excel_picks_the_largest_sheet(tmp_path):
    file_path = tmp_path / "sample.xlsx"
    with pd.ExcelWriter(file_path) as writer:
        pd.DataFrame({"note": ["read me"]}).to_excel(writer, sheet_name="README", index=False)
        pd.DataFrame({"a": range(10), "b": range(10)}).to_excel(
            writer, sheet_name="Sales_Data", index=False
        )

    with open(file_path, "rb") as file:
        loaded = load_file(file)

    assert list(loaded.columns) == ["a", "b"]
    assert len(loaded) == 10


def test_list_sheets_and_sheet_selection(tmp_path):
    file_path = tmp_path / "sample.xlsx"
    with pd.ExcelWriter(file_path) as writer:
        pd.DataFrame({"note": ["read me"]}).to_excel(writer, sheet_name="README", index=False)
        pd.DataFrame({"a": [1, 2]}).to_excel(writer, sheet_name="Sales_Data", index=False)

    with open(file_path, "rb") as file:
        assert list_sheets(file) == ["README", "Sales_Data"]
    with open(file_path, "rb") as file:
        assert list(load_file(file, sheet_name="README").columns) == ["note"]


def test_unsupported_extension_is_rejected(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError):
        with open(file_path, "rb") as file:
            load_file(file)
