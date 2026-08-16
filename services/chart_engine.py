import pandas as pd
import plotly.express as px


def _get_numeric_columns(df):
    """
    Return columns that contain numeric data.
    """

    return df.select_dtypes(
        include="number"
    ).columns.tolist()


def _get_text_columns(df):
    """
    Return categorical/text columns.
    """

    text_columns = []

    for column in df.columns:

        series = df[column]

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
            or isinstance(
                series.dtype,
                pd.CategoricalDtype
            )
        ):
            text_columns.append(column)

    return text_columns


def _get_date_columns(df):
    """
    Detect datetime columns and columns whose names
    indicate date information.
    """

    date_columns = []

    for column in df.columns:

        series = df[column]

        if pd.api.types.is_datetime64_any_dtype(series):

            date_columns.append(column)

            continue

        if "date" in str(column).lower():

            converted = pd.to_datetime(
                series,
                errors="coerce"
            )

            if converted.notna().mean() >= 0.8:

                date_columns.append(column)

    return date_columns


def create_charts(df):

    charts = []

    # --------------------------------
    # Empty dataset
    # --------------------------------

    if df is None or df.empty:

        return charts

    # --------------------------------
    # Detect column types
    # --------------------------------

    numeric_columns = _get_numeric_columns(df)

    text_columns = _get_text_columns(df)

    date_columns = _get_date_columns(df)

    # ==================================================
    # 1. BAR CHART
    # ==================================================

    if text_columns and numeric_columns:

        category = None

        value = None

        # --------------------------------
        # Prefer meaningful business categories
        # --------------------------------

        preferred_categories = [
            "Region",
            "Category",
            "Product",
            "Product_Name",
            "Customer",
            "Customer_Name"
        ]

        for candidate in preferred_categories:

            for column in text_columns:

                if column.lower() == candidate.lower():

                    category = column

                    break

            if category:

                break

        if category is None:

            category = text_columns[0]

        # --------------------------------
        # Prefer meaningful numeric measures
        # --------------------------------

        preferred_values = [
            "Total_Amount_USD",
            "Total_Amount",
            "Sales",
            "Revenue",
            "Quantity"
        ]

        for candidate in preferred_values:

            for column in numeric_columns:

                if column.lower() == candidate.lower():

                    value = column

                    break

            if value:

                break

        if value is None:

            value = numeric_columns[0]

        # --------------------------------
        # Prepare chart data
        # --------------------------------

        chart_data = (
            df[[category, value]]
            .dropna()
            .groupby(
                category,
                as_index=False
            )[value]
            .sum()
            .sort_values(
                value,
                ascending=False
            )
            .head(10)
        )

        if not chart_data.empty:

            fig = px.bar(
                chart_data,
                x=category,
                y=value,
                title=f"{value} by {category}",
                labels={
                    category: category,
                    value: value
                }
            )

            charts.append(fig)

    # ==================================================
    # 2. HISTOGRAM
    # ==================================================

    if numeric_columns:

        histogram_column = None

        preferred_histogram_columns = [
            "Total_Amount_USD",
            "Total_Amount",
            "Sales",
            "Revenue",
            "Quantity"
        ]

        for candidate in preferred_histogram_columns:

            for column in numeric_columns:

                if column.lower() == candidate.lower():

                    histogram_column = column

                    break

            if histogram_column:

                break

        if histogram_column is None:

            histogram_column = numeric_columns[0]

        histogram_data = df[
            histogram_column
        ].dropna()

        if not histogram_data.empty:

            fig = px.histogram(
                df,
                x=histogram_column,
                title=(
                    f"Distribution of "
                    f"{histogram_column}"
                ),
                nbins=30
            )

            charts.append(fig)

    # ==================================================
    # 3. LINE CHART
    # ==================================================

    if date_columns and numeric_columns:

        date_column = date_columns[0]

        value_column = None

        preferred_values = [
            "Total_Amount_USD",
            "Total_Amount",
            "Sales",
            "Revenue",
            "Quantity"
        ]

        for candidate in preferred_values:

            for column in numeric_columns:

                if column.lower() == candidate.lower():

                    value_column = column

                    break

            if value_column:

                break

        if value_column is None:

            value_column = numeric_columns[0]

        line_data = df[
            [date_column, value_column]
        ].copy()

        # --------------------------------
        # Safe date conversion
        # --------------------------------

        line_data[date_column] = pd.to_datetime(
            line_data[date_column],
            errors="coerce"
        )

        # --------------------------------
        # Safe numeric conversion
        # --------------------------------

        line_data[value_column] = pd.to_numeric(
            line_data[value_column],
            errors="coerce"
        )

        line_data = line_data.dropna()

        if not line_data.empty:

            line_data = (
                line_data
                .groupby(
                    date_column,
                    as_index=False
                )[value_column]
                .sum()
                .sort_values(
                    date_column
                )
            )

            if not line_data.empty:

                fig = px.line(
                    line_data,
                    x=date_column,
                    y=value_column,
                    title=(
                        f"{value_column} "
                        "over time"
                    ),
                    markers=True
                )

                charts.append(fig)

    # ==================================================
    # 4. SCATTER PLOT
    # ==================================================

    if len(numeric_columns) >= 2:

        x_column = None

        y_column = None

        # --------------------------------
        # Prefer business-related X values
        # --------------------------------

        preferred_x = [
            "Quantity",
            "Qty",
            "Units",
            "Unit_Price_USD",
            "Unit_Price"
        ]

        # --------------------------------
        # Prefer business-related Y values
        # --------------------------------

        preferred_y = [
            "Total_Amount_USD",
            "Total_Amount",
            "Sales",
            "Revenue"
        ]

        # --------------------------------
        # Find X column
        # --------------------------------

        for candidate in preferred_x:

            for column in numeric_columns:

                if column.lower() == candidate.lower():

                    x_column = column

                    break

            if x_column:

                break

        # --------------------------------
        # Find Y column
        # --------------------------------

        for candidate in preferred_y:

            for column in numeric_columns:

                if column.lower() == candidate.lower():

                    y_column = column

                    break

            if y_column:

                break

        # --------------------------------
        # Fallback X
        # --------------------------------

        if x_column is None:

            x_column = numeric_columns[0]

        # --------------------------------
        # Fallback Y
        # --------------------------------

        if y_column is None:

            for column in numeric_columns:

                if column != x_column:

                    y_column = column

                    break

        # --------------------------------
        # Create scatter data
        # --------------------------------

        if y_column:

            scatter_data = df[
                [x_column, y_column]
            ].copy()

            scatter_data[x_column] = pd.to_numeric(
                scatter_data[x_column],
                errors="coerce"
            )

            scatter_data[y_column] = pd.to_numeric(
                scatter_data[y_column],
                errors="coerce"
            )

            scatter_data = (
                scatter_data
                .dropna()
            )

            if not scatter_data.empty:

                fig = px.scatter(
                    scatter_data,
                    x=x_column,
                    y=y_column,
                    title=(
                        f"{y_column} "
                        f"vs {x_column}"
                    )
                )

                charts.append(fig)

    return charts