import pandas as pd


def load_file(file):

    filename = file.name.lower().strip()

    if filename.endswith(".csv"):
        df = pd.read_csv(file)

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(file)

    else:
        raise ValueError(
            "Unsupported file format. "
            "Please upload a CSV or XLSX file."
        )

    if df.empty:
        raise ValueError(
            "The uploaded file contains no data."
        )

    # Remove completely empty columns
    df = df.dropna(
        axis=1,
        how="all"
    )

    # Remove completely empty rows
    df = df.dropna(
        axis=0,
        how="all"
    )

    if df.empty:
        raise ValueError(
            "The uploaded file contains no usable data."
        )

    return df