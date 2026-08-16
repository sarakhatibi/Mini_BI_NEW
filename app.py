import streamlit as st
import pandas as pd

from services.data_loader import load_file
from services.data_analyzer import analyze_dataset
from services.kpi_engine import calculate_kpis
from services.chart_engine import create_charts
from services.insight_engine import generate_insights

from components.dashboard import (
    show_header,
    show_kpis,
    show_insights,
    show_charts
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Mini BI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
from app_css_inject import inject_style
# انتخاب تم (در سایدبار یا ثابت)
theme_map = {"خنثی (پیش‌فرض)": "muted", "پررنگ": "vibrant", "تاریک": "dark"}
theme_choice = st.sidebar.selectbox("ظاهر صفحه", ["خنثی (پیش‌فرض)", "پررنگ", "تاریک"])
inject_style(theme=theme_map[theme_choice])
# ==================================================
# HEADER
# ==================================================

show_header()

st.write(
    "فایل Excel یا CSV خود را بارگذاری کنید تا داده‌ها "
    "تحلیل و به صورت تعاملی نمایش داده شوند."
)


# ==================================================
# FILE UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "📂 انتخاب فایل داده",
    type=["csv", "xlsx"],
    help="فایل CSV یا Excel خود را انتخاب کنید."
)


# ==================================================
# MAIN APPLICATION
# ==================================================

if uploaded_file is not None:

    try:

        # ==================================================
        # 1. LOAD DATA
        # ==================================================

        data = load_file(uploaded_file)

        if data is None or data.empty:

            st.warning(
                "⚠️ فایل خالی است یا داده قابل پردازشی در آن پیدا نشد."
            )

            st.stop()


        # ==================================================
        # 2. ANALYZE DATASET
        # ==================================================

        analysis = analyze_dataset(data)


        # ==================================================
        # 3. SIDEBAR
        # ==================================================

        st.sidebar.title("🎛️ کنترل‌های تحلیل")

        st.sidebar.caption(
            "فیلترها و تنظیمات نمایش داده‌ها"
        )

        st.sidebar.divider()


        # ==================================================
        # 4. RESET FILTERS
        # ==================================================

        if st.sidebar.button(
            "🔄 بازنشانی همه فیلترها",
            use_container_width=True
        ):

            keys_to_delete = [
                key
                for key in st.session_state.keys()
                if key.startswith("filter_")
            ]

            for key in keys_to_delete:
                del st.session_state[key]

            st.rerun()


        # ==================================================
        # 5. START WITH ORIGINAL DATA
        # ==================================================

        filtered_data = data.copy()


        # ==================================================
        # 6. TEXT / CATEGORY FILTERS
        # ==================================================

        st.sidebar.subheader(
            "🏷️ فیلترهای دسته‌بندی"
        )

        text_columns = analysis.get(
            "text_columns",
            []
        )

        for column in text_columns:

            values = (
                data[column]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            values = sorted(
                [value for value in values if value != ""]
            )

            # Only show reasonable-size categorical filters
            if 0 < len(values) <= 50:

                selected_values = st.sidebar.multiselect(
                    f"{column}",
                    values,
                    key=f"filter_text_{column}"
                )

                if selected_values:

                    filtered_data = filtered_data[
                        filtered_data[column]
                        .astype(str)
                        .str.strip()
                        .isin(selected_values)
                    ]


        # ==================================================
        # 7. NUMERIC FILTERS
        # ==================================================

        numeric_columns = analysis.get(
            "numeric_columns",
            []
        )

        if numeric_columns:

            st.sidebar.divider()

            st.sidebar.subheader(
                "🔢 فیلترهای عددی"
            )

        for column in numeric_columns:

            numeric_series = pd.to_numeric(
                data[column],
                errors="coerce"
            ).dropna()

            if numeric_series.empty:
                continue

            minimum = float(
                numeric_series.min()
            )

            maximum = float(
                numeric_series.max()
            )

            if minimum == maximum:
                continue

            selected_range = st.sidebar.slider(
                column,
                min_value=minimum,
                max_value=maximum,
                value=(minimum, maximum),
                key=f"filter_numeric_{column}"
            )

            filtered_numeric = pd.to_numeric(
                filtered_data[column],
                errors="coerce"
            )

            filtered_data = filtered_data[
                filtered_numeric.between(
                    selected_range[0],
                    selected_range[1]
                )
            ]


        # ==================================================
        # 8. DATE FILTERS
        # ==================================================

        date_columns = analysis.get(
            "date_columns",
            []
        )

        if date_columns:

            st.sidebar.divider()

            st.sidebar.subheader(
                "📅 فیلتر تاریخ"
            )

        for column in date_columns:

            converted_dates = pd.to_datetime(
                data[column],
                errors="coerce"
            ).dropna()

            if converted_dates.empty:
                continue

            min_date = converted_dates.min().date()
            max_date = converted_dates.max().date()

            if min_date == max_date:
                continue

            selected_dates = st.sidebar.date_input(
                column,
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key=f"filter_date_{column}"
            )

            if (
                isinstance(selected_dates, tuple)
                and len(selected_dates) == 2
            ):

                start_date = pd.Timestamp(
                    selected_dates[0]
                )

                end_date = (
                    pd.Timestamp(
                        selected_dates[1]
                    )
                    + pd.Timedelta(days=1)
                )

                converted_filtered_dates = pd.to_datetime(
                    filtered_data[column],
                    errors="coerce"
                )

                filtered_data = filtered_data[
                    converted_filtered_dates.between(
                        start_date,
                        end_date,
                        inclusive="left"
                    )
                ]


        # ==================================================
        # 9. FILTER SUMMARY
        # ==================================================

        st.sidebar.divider()

        st.sidebar.subheader(
            "📌 وضعیت داده"
        )

        st.sidebar.metric(
            "تعداد کل رکوردها",
            f"{len(data):,}"
        )

        st.sidebar.metric(
            "رکوردهای انتخاب‌شده",
            f"{len(filtered_data):,}"
        )

        removed_rows = (
            len(data) - len(filtered_data)
        )

        st.sidebar.metric(
            "رکوردهای فیلترشده",
            f"{removed_rows:,}"
        )


        # ==================================================
        # 10. SORTING
        # ==================================================

        st.subheader(
            "⚙️ تنظیمات نمایش داده"
        )

        sort_col1, sort_col2, sort_col3 = st.columns(
            [2, 2, 1]
        )

        with sort_col1:

            sortable_columns = list(
                filtered_data.columns
            )

            sort_column = st.selectbox(
                "مرتب‌سازی بر اساس",
                options=sortable_columns,
                index=0
            )

        with sort_col2:

            sort_order = st.selectbox(
                "ترتیب",
                [
                    "صعودی",
                    "نزولی"
                ]
            )

        with sort_col3:

            st.write("")

            apply_sort = st.checkbox(
                "فعال",
                value=True
            )


        # ==================================================
        # 11. APPLY SORT
        # ==================================================

        if (
            apply_sort
            and sort_column in filtered_data.columns
        ):

            ascending = (
                sort_order == "صعودی"
            )

            try:

                filtered_data = (
                    filtered_data
                    .sort_values(
                        by=sort_column,
                        ascending=ascending,
                        na_position="last"
                    )
                )

            except Exception:

                pass


        # ==================================================
        # 12. DASHBOARD CALCULATIONS
        # ==================================================

        kpis = calculate_kpis(
            filtered_data
        )

        charts = create_charts(
            filtered_data
        )

        insights = generate_insights(
            filtered_data,
            kpis
        )


        # ==================================================
        # 13. TABS
        # ==================================================

        tab1, tab2, tab3 = st.tabs(
            [
                "📊 داشبورد",
                "🔍 کیفیت داده",
                "📋 داده‌ها"
            ]
        )


        # ==================================================
        # TAB 1 — DASHBOARD
        # ==================================================

        with tab1:

            show_kpis(
                kpis
            )

            st.divider()

            show_insights(
                insights
            )

            st.divider()

            show_charts(
                charts
            )


        # ==================================================
        # TAB 2 — DATA QUALITY
        # ==================================================

        with tab2:

            st.subheader(
                "🔍 بررسی کیفیت داده"
            )

            st.caption(
                "موارد احتمالی مربوط به کیفیت داده‌های "
                "فایل بارگذاری‌شده."
            )


            # ----------------------------------------------
            # Quality Counters
            # ----------------------------------------------

            missing_count = analysis.get(
                "total_missing",
                0
            )

            duplicate_count = analysis.get(
                "duplicate_rows",
                0
            )

            type_issue_count = len(
                analysis.get(
                    "type_issues",
                    {}
                )
            )

            unusual_issue_count = len(
                analysis.get(
                    "unusual_values",
                    {}
                )
            )

            naming_issue_count = len(
                analysis.get(
                    "naming_issues",
                    []
                )
            )

            format_issue_count = len(
                analysis.get(
                    "format_issues",
                    {}
                )
            )


            total_issues = (
                missing_count
                + duplicate_count
                + type_issue_count
                + unusual_issue_count
                + naming_issue_count
                + format_issue_count
            )


            # ----------------------------------------------
            # Quality Metrics
            # ----------------------------------------------

            q1, q2, q3, q4 = st.columns(4)

            with q1:

                st.metric(
                    "مقادیر خالی",
                    f"{missing_count:,}"
                )

            with q2:

                st.metric(
                    "رکوردهای تکراری",
                    f"{duplicate_count:,}"
                )

            with q3:

                st.metric(
                    "مشکلات شناسایی‌شده",
                    f"{total_issues:,}"
                )

            with q4:

                st.metric(
                    "تعداد ستون‌ها",
                    f'{len(data.columns):,}'
                )


            st.divider()


            # ==================================================
            # 1. MISSING VALUES
            # ==================================================

            st.subheader(
                "1️⃣ مقادیر خالی"
            )

            if missing_count > 0:

                st.warning(
                    f"{missing_count:,} مقدار خالی شناسایی شد."
                )

                missing_df = pd.DataFrame(
                    list(
                        analysis[
                            "missing_values"
                        ].items()
                    ),
                    columns=[
                        "ستون",
                        "تعداد مقادیر خالی"
                    ]
                )

                st.dataframe(
                    missing_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success(
                    "✅ هیچ مقدار خالی شناسایی نشد."
                )


            # ==================================================
            # 2. DUPLICATES
            # ==================================================

            st.subheader(
                "2️⃣ رکوردهای تکراری"
            )

            if duplicate_count > 0:

                st.warning(
                    f"{duplicate_count:,} رکورد تکراری شناسایی شد."
                )

            else:

                st.success(
                    "✅ رکورد تکراری شناسایی نشد."
                )


            # ==================================================
            # 3. TYPE ISSUES
            # ==================================================

            st.subheader(
                "3️⃣ ناسازگاری نوع داده"
            )

            if type_issue_count > 0:

                st.warning(
                    "⚠️ احتمال ناسازگاری نوع داده وجود دارد."
                )

                type_rows = []

                for column, issue in analysis[
                    "type_issues"
                ].items():

                    type_rows.append(
                        {
                            "ستون": column,
                            "مشکل": issue
                        }
                    )

                st.dataframe(
                    pd.DataFrame(type_rows),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success(
                    "✅ ناسازگاری نوع داده شناسایی نشد."
                )


            # ==================================================
            # 4. UNUSUAL VALUES
            # ==================================================

            st.subheader(
                "4️⃣ مقادیر غیرعادی"
            )

            if unusual_issue_count > 0:

                st.warning(
                    "⚠️ برخی مقادیر ممکن است غیرعادی باشند."
                )

                unusual_rows = []

                for column, issues in analysis[
                    "unusual_values"
                ].items():

                    for issue in issues:

                        unusual_rows.append(
                            {
                                "ستون": column,
                                "مشکل": issue
                            }
                        )

                st.dataframe(
                    pd.DataFrame(
                        unusual_rows
                    ),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success(
                    "✅ مقدار غیرعادی شناسایی نشد."
                )


            # ==================================================
            # 5. NAMING ISSUES
            # ==================================================

            st.subheader(
                "5️⃣ مشکلات نام‌گذاری ستون‌ها"
            )

            if naming_issue_count > 0:

                st.warning(
                    "⚠️ برخی نام ستون‌ها نیاز به بررسی دارند."
                )

                naming_df = pd.DataFrame(
                    analysis[
                        "naming_issues"
                    ],
                    columns=["مشکل"]
                )

                st.dataframe(
                    naming_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success(
                    "✅ مشکل نام‌گذاری شناسایی نشد."
                )


            # ==================================================
            # 6. FORMAT ISSUES
            # ==================================================

            st.subheader(
                "6️⃣ مشکلات قالب تاریخ و عدد"
            )

            if format_issue_count > 0:

                st.warning(
                    "⚠️ ناسازگاری در قالب تاریخ یا عدد شناسایی شد."
                )

                format_rows = []

                for column, issue in analysis[
                    "format_issues"
                ].items():

                    format_rows.append(
                        {
                            "ستون": column,
                            "مشکل": issue
                        }
                    )

                st.dataframe(
                    pd.DataFrame(
                        format_rows
                    ),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success(
                    "✅ مشکل قالب تاریخ یا عدد شناسایی نشد."
                )


            # ==================================================
            # DATA QUALITY POLICY
            # ==================================================

            st.divider()

            st.subheader(
                "📌 نحوه مدیریت کیفیت داده"
            )

            st.info(
                "سیستم مشکلات احتمالی داده را شناسایی و گزارش می‌کند؛ "
                "رکوردهای اصلی به صورت خودکار حذف یا تغییر داده نمی‌شوند."
            )


        # ==================================================
        # TAB 3 — DATA
        # ==================================================

        with tab3:

            st.subheader(
                "📋 داده‌های پردازش‌شده"
            )

            # ----------------------------------------------
            # Dataset summary
            # ----------------------------------------------

            info1, info2, info3 = st.columns(3)

            with info1:

                st.metric(
                    "تعداد رکورد",
                    f"{len(filtered_data):,}"
                )

            with info2:

                st.metric(
                    "تعداد ستون",
                    f"{len(filtered_data.columns):,}"
                )

            with info3:

                st.metric(
                    "تعداد رکورد حذف‌شده توسط فیلتر",
                    f"{len(data) - len(filtered_data):,}"
                )


            st.divider()


            # ----------------------------------------------
            # Display controls
            # ----------------------------------------------

            data_col1, data_col2 = st.columns(
                [2, 2]
            )

            with data_col1:

                search_text = st.text_input(
                    "🔎 جستجو در داده‌ها",
                    placeholder="عبارت موردنظر را وارد کنید..."
                )

            with data_col2:

                rows_to_show = st.selectbox(
                    "تعداد ردیف قابل نمایش",
                    [
                        10,
                        25,
                        50,
                        100,
                        250,
                        500
                    ],
                    index=2
                )


            # ----------------------------------------------
            # Search
            # ----------------------------------------------

            display_data = filtered_data.copy()

            if search_text.strip():

                search_value = (
                    search_text
                    .strip()
                    .lower()
                )

                mask = display_data.astype(
                    str
                ).apply(
                    lambda column:
                    column.str.lower().str.contains(
                        search_value,
                        na=False,
                        regex=False
                    )
                ).any(
                    axis=1
                )

                display_data = display_data[
                    mask
                ]


            # ----------------------------------------------
            # Data table
            # ----------------------------------------------

            st.caption(
                f"نمایش {min(len(display_data), rows_to_show):,} "
                f"ردیف از {len(display_data):,} ردیف"
            )

            st.dataframe(
                display_data.head(
                    rows_to_show
                ),
                use_container_width=True,
                hide_index=True
            )


    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except Exception as error:

        st.error(
            "❌ در پردازش فایل مشکلی ایجاد شد."
        )

        st.exception(
            error
        )


# ==================================================
# EMPTY STATE
# ==================================================

else:

    st.info(
        "👆 برای شروع، یک فایل CSV یا Excel بارگذاری کنید."
    )

    st.markdown(
        """
        ### امکانات سیستم

        - 📊 محاسبه شاخص‌های کلیدی عملکرد
        - 📈 تولید نمودارهای تحلیلی
        - 💡 تولید بینش مدیریتی
        - 🔍 بررسی کیفیت داده
        - 🎛️ فیلتر داده‌ها
        - 🔢 فیلتر عددی
        - 📅 فیلتر تاریخ
        - ↕️ مرتب‌سازی داده‌ها
        - 🔎 جستجو در جدول
        - 📋 مشاهده داده‌های پردازش‌شده
        """
    )