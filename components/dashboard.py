"""Reusable dashboard building blocks."""

import streamlit as st

KPI_COLUMNS = 4
LEVEL_RENDERERS = {
    "positive": st.success,
    "warning": st.warning,
    "info": st.info,
}


def show_header():
    st.title("📊 پلتفرم تحلیل داده مدیریتی")
    st.caption(
        "فایل فروش خود را بارگذاری کنید؛ سیستم داده را پاک‌سازی، تحلیل و "
        "به شاخص، نمودار و پیشنهاد مدیریتی تبدیل می‌کند."
    )


def show_kpis(kpi_result):
    st.subheader("📌 شاخص‌های کلیدی")

    kpis = getattr(kpi_result, "kpis", [])
    if not kpis:
        st.info("برای این داده شاخص قابل محاسبه‌ای شناسایی نشد.")
        return

    for start in range(0, len(kpis), KPI_COLUMNS):
        row = kpis[start:start + KPI_COLUMNS]
        columns = st.columns(len(row))
        for column, kpi in zip(columns, row):
            with column:
                st.metric(label=kpi.label, value=kpi.display, help=kpi.description)


def show_insights(insights):
    st.subheader("💡 بینش‌های مدیریتی")

    if not insights:
        st.info("برای داده فعلی بینشی تولید نشد.")
        return

    for insight in insights:
        renderer = LEVEL_RENDERERS.get(insight.level, st.info)
        message = insight.text
        if insight.evidence:
            message += f"  \n\n`{insight.evidence}`"
        renderer(message)


def show_charts(charts):
    st.subheader("📈 نمودارهای پیشنهادی")

    if not charts:
        st.info("برای داده فعلی نمودار مناسبی شناسایی نشد.")
        return

    for index in range(0, len(charts), 2):
        row = charts[index:index + 2]
        columns = st.columns(len(row))
        for column, chart in zip(columns, row):
            with column:
                st.plotly_chart(chart.figure, use_container_width=True)
                st.caption(chart.description)
