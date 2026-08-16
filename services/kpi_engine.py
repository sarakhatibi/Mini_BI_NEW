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
    Convert a Series to numeric values safely.

    Invalid values become NaN.
    """

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def calculate_kpis(df):

    kpis = {
        "total_rows": 0
    }

    # ==================================================
    # 0. BASIC VALIDATION
    # ==================================================

    if df is None:
        return kpis

    if not isinstance(
        df,
        pd.DataFrame
    ):
        return kpis

    if df.empty:
        return kpis

    # ==================================================
    # 1. TOTAL RECORDS
    # ==================================================

    kpis["total_rows"] = len(df)

    # ==================================================
    # 2. QUANTITY
    # ==================================================

    quantity_column = _find_column(
        df.columns,
        [
            "Quantity",
            "Qty",
            "Units",
            "Unit_Count"
        ]
    )

    if quantity_column:

        quantity = _safe_numeric(
            df[quantity_column]
        )

        valid_quantity = quantity.dropna()

        if not valid_quantity.empty:

            kpis[
                "total_quantity"
            ] = valid_quantity.sum()

            kpis[
                "quantity_column"
            ] = quantity_column

    # ==================================================
    # 3. SALES
    # ==================================================

    sales_column = _find_column(
        df.columns,
        [
            "Total_Amount_USD",
            "Total_Amount",
            "Sales",
            "Revenue",
            "Revenue_USD"
        ]
    )

    if sales_column:

        sales = _safe_numeric(
            df[sales_column]
        )

        valid_sales = sales.dropna()

        if not valid_sales.empty:

            kpis[
                "total_sales"
            ] = valid_sales.sum()

            kpis[
                "average_order_value"
            ] = valid_sales.mean()

            kpis[
                "sales_column"
            ] = sales_column

            kpis[
                "valid_sales_records"
            ] = len(valid_sales)

            kpis[
                "invalid_sales_records"
            ] = (
                len(sales)
                - len(valid_sales)
            )

    # ==================================================
    # 4. MINIMUM SALES
    # ==================================================

    if sales_column:

        if not valid_sales.empty:

            kpis[
                "minimum_sale"
            ] = valid_sales.min()

    # ==================================================
    # 5. MAXIMUM SALES
    # ==================================================

    if sales_column:

        if not valid_sales.empty:

            kpis[
                "maximum_sale"
            ] = valid_sales.max()

    # ==================================================
    # 6. MEDIAN SALES
    # ==================================================

    if sales_column:

        if not valid_sales.empty:

            kpis[
                "median_sale"
            ] = valid_sales.median()

    # ==================================================
    # 7. ZERO / NEGATIVE SALES
    # ==================================================

    if sales_column:

        if not valid_sales.empty:

            kpis[
                "zero_sales_records"
            ] = int(
                (valid_sales == 0).sum()
            )

            kpis[
                "negative_sales_records"
            ] = int(
                (valid_sales < 0).sum()
            )

    # ==================================================
    # 8. QUANTITY QUALITY
    # ==================================================

    if quantity_column:

        if not valid_quantity.empty:

            kpis[
                "zero_quantity_records"
            ] = int(
                (valid_quantity == 0).sum()
            )

            kpis[
                "negative_quantity_records"
            ] = int(
                (valid_quantity < 0).sum()
            )

    # ==================================================
    # 9. UNIQUE CUSTOMERS
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

    if customer_column:

        customers = (
            df[customer_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        # Ignore empty customer names
        customers = customers[
            customers != ""
        ]

        if not customers.empty:

            kpis[
                "unique_customers"
            ] = int(
                customers.nunique()
            )

            kpis[
                "customer_column"
            ] = customer_column

    # ==================================================
    # 10. UNIQUE CATEGORIES
    # ==================================================

    category_column = _find_column(
        df.columns,
        [
            "Category",
            "Product",
            "Product_Name",
            "Region"
        ]
    )

    if category_column:

        categories = (
            df[category_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        # Ignore empty category names
        categories = categories[
            categories != ""
        ]

        if not categories.empty:

            kpis[
                "unique_categories"
            ] = int(
                categories.nunique()
            )

            kpis[
                "category_column"
            ] = category_column

    # ==================================================
    # 11. RETURN
    # ==================================================

    return kpis