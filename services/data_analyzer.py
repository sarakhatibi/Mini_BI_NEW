import pandas as pd


def analyze_dataset(df):

    # --------------------------------
    # 0. Basic Dataset Validation
    # --------------------------------

    if df is None:
        raise ValueError(
            "Dataset is None."
        )

    if not isinstance(df, pd.DataFrame):
        raise ValueError(
            "Input data must be a pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Dataset is empty."
        )

    if len(df.columns) == 0:
        raise ValueError(
            "Dataset contains no columns."
        )

    date_columns = []
    numeric_columns = []
    text_columns = []

    # --------------------------------
    # 1. Detect column types
    # --------------------------------

    for column in df.columns:
        series = df[column]

        if pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(column)

        elif pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)

        elif "date" in str(column).lower():
            converted = pd.to_datetime(
                series,
                errors="coerce"
            )

            if converted.notna().mean() >= 0.8:
                date_columns.append(column)
            else:
                text_columns.append(column)

        else:
            text_columns.append(column)

    # --------------------------------
    # 2. Missing Values
    # --------------------------------

    missing_values = df.isna().sum()

    missing_values = missing_values[
        missing_values > 0
    ]

    # --------------------------------
    # 3. Duplicate Rows
    # --------------------------------

    duplicate_rows = int(
        df.duplicated().sum()
    )

    # --------------------------------
    # 4. Type Inconsistency
    # --------------------------------

    type_issues = {}

    for column in df.columns:

        series = df[column]

        if series.dtype == "object":

            non_empty = (
                series
                .dropna()
                .astype(str)
                .str.strip()
            )

            if len(non_empty) == 0:
                continue

            numeric_converted = pd.to_numeric(
                non_empty,
                errors="coerce"
            )

            numeric_ratio = (
                numeric_converted.notna().mean()
            )

            if 0.8 <= numeric_ratio < 1:

                type_issues[column] = (
                    "Mostly numeric values but some "
                    "values are stored in a different format."
                )

    # --------------------------------
    # 5. Unusual Values
    # --------------------------------

    unusual_values = {}

    for column in numeric_columns:

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if series.empty:
            continue

        issues = []

        # Negative values
        if (series < 0).any():

            issues.append(
                "negative values"
            )

        # Percentage-like columns
        if any(
            keyword in str(column).lower()
            for keyword in [
                "percent",
                "percentage",
                "discount",
                "tax"
            ]
        ):

            if (series > 100).any():

                issues.append(
                    "values greater than 100"
                )

        if issues:

            unusual_values[column] = issues

    # --------------------------------
    # 6. Naming Irregularities
    # --------------------------------

    naming_issues = []

    for column in df.columns:

        column_name = str(column)

        if column_name != column_name.strip():

            naming_issues.append(
                f"{column}: leading/trailing spaces"
            )

        if " " in column_name:

            naming_issues.append(
                f"{column}: contains spaces"
            )

    # --------------------------------
    # 7. Date / Number Format Issues
    # --------------------------------

    format_issues = {}

    for column in df.columns:

        series = df[column].dropna()

        if series.empty:
            continue

        # Convert values to string for format inspection
        values = series.astype(str).str.strip()

        # --------------------------------
        # Numeric format detection
        # --------------------------------

        numeric_values = pd.to_numeric(
            values,
            errors="coerce"
        )

        numeric_ratio = (
            numeric_values.notna().mean()
        )

        # If most values are numeric-like,
        # check whether some values contain
        # symbols, units or percentage signs.
        if numeric_ratio >= 0.8:

            problematic_values = values[
                numeric_values.isna()
            ]

            if not problematic_values.empty:

                examples = (
                    problematic_values
                    .head(3)
                    .tolist()
                )

                format_issues[column] = (
                    "Inconsistent numeric format. "
                    f"Examples: {examples}"
                )

                continue

        # --------------------------------
        # Percentage format detection
        # --------------------------------

        percent_mask = values.str.contains(
            "%",
            regex=False
        )

        if percent_mask.any():

            without_percent = (
                values
                .str.replace(
                    "%",
                    "",
                    regex=False
                )
            )

            converted_percent = pd.to_numeric(
                without_percent,
                errors="coerce"
            )

            if converted_percent.notna().any():

                if column not in format_issues:

                    format_issues[column] = (
                        "Percentage values use "
                        "a mixed format."
                    )

        # --------------------------------
        # Date format detection
        # --------------------------------

        if "date" in str(column).lower():

            parsed_dates = pd.to_datetime(
                values,
                errors="coerce"
            )

            valid_ratio = (
                parsed_dates.notna().mean()
            )

            if 0 < valid_ratio < 1:

                format_issues[column] = (
                    "Some date values use "
                    "an inconsistent format."
                )

    # --------------------------------
    # 8. Return Analysis
    # --------------------------------

    return {

        "rows": len(df),

        "columns": len(df.columns),

        "column_names": list(
            df.columns
        ),

        "missing_values": (
            missing_values.to_dict()
        ),

        "total_missing": int(
            missing_values.sum()
        ),

        "duplicate_rows": duplicate_rows,

        "data_types": (
            df.dtypes
            .astype(str)
            .to_dict()
        ),

        "numeric_columns": numeric_columns,

        "text_columns": text_columns,

        "date_columns": date_columns,

        "type_issues": type_issues,

        "unusual_values": unusual_values,

        "naming_issues": naming_issues,

        "format_issues": format_issues
    }