"""File ingestion for CSV and Excel uploads."""

import io

import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1256", "latin-1")
CSV_SEPARATORS = (None, ",", ";", "\t", "|")


def _read_bytes(file) -> bytes:
    if hasattr(file, "getvalue"):
        return file.getvalue()
    if hasattr(file, "read"):
        if hasattr(file, "seek"):
            file.seek(0)
        return file.read()
    with open(file, "rb") as handle:
        return handle.read()


def list_sheets(file) -> list:
    """Return the sheet names of an Excel file (empty list for CSV)."""
    name = str(getattr(file, "name", file)).lower().strip()
    if not name.endswith((".xlsx", ".xls")):
        return []
    return pd.ExcelFile(io.BytesIO(_read_bytes(file))).sheet_names


def _read_csv(content: bytes) -> pd.DataFrame:
    last_error = None
    for encoding in CSV_ENCODINGS:
        for separator in CSV_SEPARATORS:
            try:
                frame = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    sep=separator,
                    engine="python" if separator is None else "c",
                )
            except Exception as error:  # noqa: BLE001 - try the next combination
                last_error = error
                continue
            if frame.shape[1] > 1 or separator == CSV_SEPARATORS[-1]:
                return frame
    raise ValueError(f"CSV file could not be parsed: {last_error}")


def load_file(file, sheet_name=None) -> pd.DataFrame:
    """Read an uploaded CSV/Excel file into a DataFrame.

    The largest sheet is used when the workbook has several sheets and the
    caller did not pick one.
    """
    name = str(getattr(file, "name", file)).lower().strip()
    content = _read_bytes(file)

    if name.endswith(".csv"):
        df = _read_csv(content)
    elif name.endswith((".xlsx", ".xls")):
        workbook = pd.ExcelFile(io.BytesIO(content))
        if sheet_name is None:
            frames = {sheet: workbook.parse(sheet) for sheet in workbook.sheet_names}
            sheet_name = max(frames, key=lambda sheet: frames[sheet].size)
            df = frames[sheet_name]
        else:
            df = workbook.parse(sheet_name)
    else:
        raise ValueError(
            "فرمت فایل پشتیبانی نمی‌شود. لطفاً فایل CSV یا Excel بارگذاری کنید."
        )

    if df.empty:
        raise ValueError("فایل بارگذاری‌شده هیچ داده‌ای ندارد.")

    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

    if df.empty:
        raise ValueError("فایل بارگذاری‌شده داده قابل استفاده‌ای ندارد.")

    return df
