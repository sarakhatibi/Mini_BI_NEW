import streamlit as st


# ==================================================
# HEADER
# ==================================================

def show_header():
    st.title("📊 Mini BI Analytics")

    st.caption(
        "Interactive Business Intelligence Dashboard"
    )


# ==================================================
# KPI CARDS
# ==================================================

def show_kpis(kpis):

    st.subheader("📌 Key Performance Indicators")

    # --------------------------------
    # Build available KPI cards
    # --------------------------------

    kpi_items = []

    # Total Records
    if "total_rows" in kpis:

        kpi_items.append(
            (
                "Total Records",
                f'{kpis["total_rows"]:,}'
            )
        )

    # Total Sales
    if "total_sales" in kpis:

        kpi_items.append(
            (
                "Total Sales",
                f'${kpis["total_sales"]:,.2f}'
            )
        )

    # Total Quantity
    if "total_quantity" in kpis:

        kpi_items.append(
            (
                "Total Quantity",
                f'{kpis["total_quantity"]:,.0f}'
            )
        )

    # Average Order Value
    if "average_order_value" in kpis:

        kpi_items.append(
            (
                "Average Order Value",
                f'${kpis["average_order_value"]:,.2f}'
            )
        )

    # Unique Customers
    if "unique_customers" in kpis:

        kpi_items.append(
            (
                "Unique Customers",
                f'{kpis["unique_customers"]:,}'
            )
        )

    # Unique Products
    if "unique_products" in kpis:

        kpi_items.append(
            (
                "Unique Products",
                f'{kpis["unique_products"]:,}'
            )
        )

    # --------------------------------
    # No KPI available
    # --------------------------------

    if not kpi_items:

        st.info(
            "No suitable KPIs could be calculated "
            "from this dataset."
        )

        return

    # --------------------------------
    # Display KPI cards
    # --------------------------------

    number_of_columns = min(
        len(kpi_items),
        4
    )

    columns = st.columns(
        number_of_columns
    )

    for index, (label, value) in enumerate(
        kpi_items
    ):

        with columns[
            index % number_of_columns
        ]:

            st.metric(
                label=label,
                value=value
            )


# ==================================================
# MANAGEMENT INSIGHTS
# ==================================================

def show_insights(insights):

    st.subheader(
        "💡 Management Insights"
    )

    if not insights:

        st.info(
            "No management insights are available "
            "for the current dataset."
        )

        return

    # --------------------------------
    # Display insights
    # --------------------------------

    for index, insight in enumerate(
        insights,
        start=1
    ):

        st.info(
            f"**Insight {index}:** {insight}"
        )


# ==================================================
# CHARTS
# ==================================================

def show_charts(charts):

    st.subheader(
        "📈 Visualizations"
    )

    if not charts:

        st.info(
            "No suitable visualizations were found "
            "for the current dataset."
        )

        return

    # --------------------------------
    # Display charts in two columns
    # --------------------------------

    chart_columns = st.columns(2)

    for index, chart in enumerate(charts):

        with chart_columns[
            index % 2
        ]:

            st.plotly_chart(
                chart,
                use_container_width=True
            )