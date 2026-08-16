import pandas as pd


def _find_column(columns, candidates):
    """
    Find the first matching column from candidate names.

    Matching is case-insensitive and ignores
    leading/trailing spaces.
    """

    normalized = {
        str(column).strip().lower(): column
        for column in columns
    }

    for candidate in candidates:

        key = (
            str(candidate)
            .strip()
            .lower()
        )

        if key in normalized:
            return normalized[key]

    return None


def _safe_numeric(series):
    """
    Safely convert a Series to numeric values.

    Invalid values become NaN.
    """

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def _is_valid_number(value):
    """
    Check whether a value is a valid finite number.
    """

    if value is None:
        return False

    if pd.isna(value):
        return False

    return (
        pd.api.types.is_number(value)
        and pd.api.types.is_float(value)
        or pd.api.types.is_integer(value)
    )


def generate_insights(df, kpis):

    insights = []

    # ==================================================
    # 0. BASIC VALIDATION
    # ==================================================

    if df is None:
        return insights

    if not isinstance(
        df,
        pd.DataFrame
    ):
        return insights

    if df.empty:
        return insights

    if kpis is None:
        kpis = {}

    # ==================================================
    # 1. SALES INSIGHT
    # ==================================================

    if "total_sales" in kpis:

        total_sales = kpis[
            "total_sales"
        ]

        if _is_valid_number(
            total_sales
        ):

            insights.append(
                f"Total sales are "
                f"${total_sales:,.2f}."
            )

    # ==================================================
    # 2. QUANTITY INSIGHT
    # ==================================================

    if "total_quantity" in kpis:

        total_quantity = kpis[
            "total_quantity"
        ]

        if _is_valid_number(
            total_quantity
        ):

            insights.append(
                f"Total quantity sold is "
                f"{total_quantity:,.0f}."
            )

    # ==================================================
    # 3. AVERAGE ORDER VALUE
    # ==================================================

    if "average_order_value" in kpis:

        average_order = kpis[
            "average_order_value"
        ]

        if _is_valid_number(
            average_order
        ):

            insights.append(
                f"Average order value is "
                f"${average_order:,.2f}."
            )

    # ==================================================
    # 4. FIND SALES COLUMN
    # ==================================================

    sales_column = kpis.get(
        "sales_column"
    )

    if sales_column is None:

        sales_column = _find_column(
            df.columns,
            [
                "Total_Amount_USD",
                "Total_Amount",
                "Sales",
                "Revenue"
            ]
        )

    # ==================================================
    # 5. HIGHEST TRANSACTION
    # ==================================================

    if (
        sales_column
        and sales_column in df.columns
    ):

        sales = _safe_numeric(
            df[sales_column]
        ).dropna()

        if not sales.empty:

            highest = sales.max()

            if pd.notna(highest):

                insights.append(
                    f"The highest individual "
                    f"transaction is "
                    f"${highest:,.2f}."
                )

                # --------------------------------
                # Compare highest with average
                # --------------------------------

                average = sales.mean()

                if (
                    pd.notna(average)
                    and average > 0
                ):

                    ratio = (
                        highest / average
                    )

                    if ratio >= 3:

                        insights.append(
                            "The highest transaction is "
                            "significantly above the "
                            "average order value."
                        )

    # ==================================================
    # 6. TOP CATEGORY
    # ==================================================

    category_column = _find_column(
        df.columns,
        [
            "Category",
            "Region",
            "Product",
            "Product_Name"
        ]
    )

    if (
        category_column
        and sales_column
        and sales_column in df.columns
    ):

        category_data = df[
            [
                category_column,
                sales_column
            ]
        ].copy()

        category_data[
            sales_column
        ] = _safe_numeric(
            category_data[
                sales_column
            ]
        )

        category_data[
            category_column
        ] = (
            category_data[
                category_column
            ]
            .astype(str)
            .str.strip()
        )

        category_data = category_data[
            category_data[
                category_column
            ].ne("")
        ]

        category_data = (
            category_data
            .dropna(
                subset=[
                    sales_column
                ]
            )
        )

        if not category_data.empty:

            grouped = (
                category_data
                .groupby(
                    category_column
                )[sales_column]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            if not grouped.empty:

                top_category = (
                    grouped.index[0]
                )

                top_sales = (
                    grouped.iloc[0]
                )

                if pd.notna(
                    top_sales
                ):

                    insights.append(
                        f"The highest sales "
                        f"contribution comes from "
                        f"{category_column} "
                        f"'{top_category}', with "
                        f"${top_sales:,.2f} in sales."
                    )

    # ==================================================
    # 7. TOP CUSTOMER
    # ==================================================

    customer_column = _find_column(
        df.columns,
        [
            "Customer",
            "Customer_Name",
            "Client",
            "Client_Name"
        ]
    )

    if (
        customer_column
        and sales_column
        and sales_column in df.columns
    ):

        customer_data = df[
            [
                customer_column,
                sales_column
            ]
        ].copy()

        customer_data[
            sales_column
        ] = _safe_numeric(
            customer_data[
                sales_column
            ]
        )

        customer_data[
            customer_column
        ] = (
            customer_data[
                customer_column
            ]
            .astype(str)
            .str.strip()
        )

        customer_data = customer_data[
            customer_data[
                customer_column
            ].ne("")
        ]

        customer_data = (
            customer_data
            .dropna(
                subset=[
                    sales_column
                ]
            )
        )

        if not customer_data.empty:

            customer_sales = (
                customer_data
                .groupby(
                    customer_column
                )[sales_column]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            if not customer_sales.empty:

                top_customer = (
                    customer_sales.index[0]
                )

                top_customer_sales = (
                    customer_sales.iloc[0]
                )

                if pd.notna(
                    top_customer_sales
                ):

                    insights.append(
                        f"The highest-value "
                        f"customer is "
                        f"'{top_customer}', "
                        f"generating "
                        f"${top_customer_sales:,.2f}."
                    )

    # ==================================================
    # 8. DATASET SIZE
    # ==================================================

    insights.append(
        f"The current analysis is based "
        f"on {len(df):,} records."
    )

    return insights