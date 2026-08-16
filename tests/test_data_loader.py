import pandas as pd

from services.data_loader import load_file


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