"""Mini BI Analytics — upload a sales file and get a management dashboard."""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from app_css_inject import inject_style
from components.dashboard import show_charts, show_header, show_insights, show_kpis
from services.chart_engine import create_charts
from services.data_loader import load_file
from services.insight_engine import generate_insights
from services.kpi_engine import calculate_kpis
from services.pipeline import build_analysis

SAMPLE_FILE = Path(__file__).parent / "data" / "Test_Dataset.xlsx"
MAX_FILTER_OPTIONS = 50
THEME_OPTIONS = {"خنثی (پیش‌فرض)": "muted", "پررنگ": "vibrant", "تاریک": "dark"}

st.set_page_config(
    page_title="Mini BI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="در حال پاک‌سازی و تحلیل داده...")
def prepare_analysis(content: bytes, filename: str, sheet_name=None):
    """Load and analyse an uploaded file. Cached on the file content."""
    buffer = io.BytesIO(content)
    buffer.name = filename
    raw = load_file(buffer, sheet_name=sheet_name)
    return build_analysis(raw)


def _apply_category_filters(data: pd.DataFrame, source: pd.DataFrame, columns) -> pd.DataFrame:
    for column in columns:
        values = sorted(source[column].dropna().astype(str).unique().tolist())
        if not 0 < len(values) <= MAX_FILTER_OPTIONS:
            continue
        selected = st.sidebar.multiselect(column, values, key=f"filter_text_{column}")
        if selected:
            data = data[data[column].astype(str).isin(selected)]
    return data


def _apply_numeric_filters(data: pd.DataFrame, source: pd.DataFrame, columns) -> pd.DataFrame:
    for column in columns:
        values = pd.to_numeric(source[column], errors="coerce").dropna()
        if values.empty:
            continue
        minimum, maximum = float(values.min()), float(values.max())
        if minimum == maximum:
            continue
        low, high = st.sidebar.slider(
            column,
            min_value=minimum,
            max_value=maximum,
            value=(minimum, maximum),
            key=f"filter_numeric_{column}",
        )
        if (low, high) != (minimum, maximum):
            numeric = pd.to_numeric(data[column], errors="coerce")
            data = data[numeric.between(low, high)]
    return data


def _apply_date_filters(data: pd.DataFrame, source: pd.DataFrame, columns) -> pd.DataFrame:
    for column in columns:
        values = pd.to_datetime(source[column], errors="coerce").dropna()
        if values.empty:
            continue
        minimum, maximum = values.min().date(), values.max().date()
        if minimum == maximum:
            continue
        selection = st.sidebar.date_input(
            column,
            value=(minimum, maximum),
            min_value=minimum,
            max_value=maximum,
            key=f"filter_date_{column}",
        )
        if isinstance(selection, tuple) and len(selection) == 2:
            start = pd.Timestamp(selection[0])
            end = pd.Timestamp(selection[1]) + pd.Timedelta(days=1)
            dates = pd.to_datetime(data[column], errors="coerce")
            data = data[dates.between(start, end, inclusive="left")]
    return data


def render_sidebar_filters(bundle) -> pd.DataFrame:
    profile = bundle.profile
    data = bundle.data

    st.sidebar.title("🎛️ فیلترها")
    if st.sidebar.button("🔄 بازنشانی فیلترها", use_container_width=True):
        for key in [key for key in st.session_state if key.startswith("filter_")]:
            del st.session_state[key]
        st.rerun()

    filtered = data.copy()

    dimensions = [
        column
        for column in profile.category_columns
        if data[column].dropna().nunique() <= MAX_FILTER_OPTIONS
    ]
    if dimensions:
        st.sidebar.subheader("🏷️ دسته‌بندی")
        filtered = _apply_category_filters(filtered, data, dimensions)

    if profile.date_columns:
        st.sidebar.subheader("📅 بازه زمانی")
        filtered = _apply_date_filters(filtered, data, profile.date_columns)

    measures = profile.measure_columns + profile.percent_columns
    if measures:
        with st.sidebar.expander("🔢 فیلترهای عددی"):
            filtered = _apply_numeric_filters(filtered, data, measures)

    st.sidebar.divider()
    st.sidebar.metric("رکوردهای انتخاب‌شده", f"{len(filtered):,}", f"{len(filtered) - len(data):,}")
    return filtered


def render_quality_tab(bundle):
    quality = bundle.quality
    cleaning = bundle.cleaning

    score = quality["score"]
    st.subheader("🔍 کیفیت داده")
    columns = st.columns(4)
    columns[0].metric("امتیاز کیفیت", f"{score:,.0f}/100")
    columns[1].metric("مقادیر خالی", f"{quality['total_missing']:,}")
    columns[2].metric("رکورد تکراری حذف‌شده", f"{quality['duplicate_rows']:,}")
    columns[3].metric("مشکلات با شدت بالا", f"{quality['high_severity']:,}")

    st.progress(min(score / 100, 1.0))
    if score >= 85:
        st.success("کیفیت داده برای تصمیم‌گیری مناسب است.")
    elif score >= 60:
        st.warning("داده قابل استفاده است اما چند مشکل نیاز به بررسی دارد.")
    else:
        st.error("کیفیت داده پایین است؛ نتایج را با احتیاط تفسیر کنید.")

    st.divider()
    st.markdown("#### مشکلات شناسایی‌شده")
    if quality["issues"]:
        st.dataframe(pd.DataFrame(quality["issues"]), use_container_width=True, hide_index=True)
    else:
        st.success("مشکل قابل توجهی در داده شناسایی نشد.")

    st.divider()
    st.markdown("#### تصمیم‌های پاک‌سازی سیستم")
    st.caption(
        "هیچ رکوردی به‌جز ردیف‌های کاملاً تکراری حذف نشده است؛ بقیه موارد فقط "
        "استانداردسازی شده‌اند تا محاسبات درست انجام شود."
    )
    actions = cleaning.actions_frame()
    if actions.empty:
        st.info("داده ورودی نیازی به اصلاح نداشت.")
    else:
        st.dataframe(actions, use_container_width=True, hide_index=True)


def render_schema_tab(bundle):
    st.subheader("🧭 نقشه ستون‌ها")
    st.caption("برداشت سیستم از معنی هر ستون؛ مبنای انتخاب شاخص‌ها و نمودارهاست.")
    st.dataframe(
        pd.DataFrame(bundle.structure["column_summary"]),
        use_container_width=True,
        hide_index=True,
    )

    profile = bundle.profile
    roles = {
        "ستون مبلغ": profile.money_column,
        "ستون مقدار": profile.quantity_column,
        "ستون تاریخ اصلی": profile.primary_date,
        "ستون مشتری": profile.customer_column,
        "ستون محصول": profile.product_column,
        "ستون منطقه": profile.region_column,
        "ستون وضعیت": profile.status_column,
        "شناسه سفارش": profile.order_id_column,
    }
    st.markdown("#### نقش‌های تشخیص داده‌شده")
    st.dataframe(
        pd.DataFrame(
            [{"نقش": key, "ستون": value or "—"} for key, value in roles.items()]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_data_tab(bundle, filtered: pd.DataFrame):
    st.subheader("📋 داده پاک‌سازی‌شده")

    search_column, rows_column, sort_column = st.columns([3, 1, 2])
    with search_column:
        query = st.text_input("🔎 جستجو", placeholder="بخشی از یک مقدار را بنویسید...")
    with rows_column:
        page_size = st.selectbox("تعداد ردیف", [25, 50, 100, 250, 500], index=1)
    with sort_column:
        sort_by = st.selectbox("مرتب‌سازی بر اساس", ["—"] + list(filtered.columns))

    display = filtered
    if query.strip():
        needle = query.strip().lower()
        mask = display.astype(str).apply(
            lambda column: column.str.lower().str.contains(needle, na=False, regex=False)
        ).any(axis=1)
        display = display[mask]

    if sort_by != "—":
        descending = st.checkbox("نزولی", value=True, key="sort_descending")
        display = display.sort_values(by=sort_by, ascending=not descending, na_position="last")

    st.caption(f"نمایش {min(len(display), page_size):,} ردیف از {len(display):,} ردیف")
    st.dataframe(display.head(page_size), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### خروجی گرفتن")
    export_columns = st.columns(2)
    export_columns[0].download_button(
        "⬇️ دانلود داده پاک‌سازی‌شده (CSV)",
        data=display.to_csv(index=False).encode("utf-8-sig"),
        file_name="cleaned_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
    export_columns[1].download_button(
        "⬇️ دانلود گزارش پاک‌سازی (CSV)",
        data=bundle.cleaning.actions_frame().to_csv(index=False).encode("utf-8-sig"),
        file_name="cleaning_report.csv",
        mime="text/csv",
        use_container_width=True,
    )


def main():
    theme = st.sidebar.selectbox("ظاهر صفحه", list(THEME_OPTIONS))
    inject_style(theme=THEME_OPTIONS[theme])

    show_header()

    uploaded_file = st.file_uploader(
        "📂 فایل داده (CSV یا Excel)",
        type=["csv", "xlsx", "xls"],
        help="فایل فروش خود را بارگذاری کنید؛ نیازی به تمیز کردن قبلی نیست.",
    )

    use_sample = False
    if uploaded_file is None:
        st.info("👆 برای شروع یک فایل بارگذاری کنید یا داده نمونه را ببینید.")
        use_sample = st.button("📈 نمایش با داده نمونه", type="primary") or st.session_state.get(
            "use_sample", False
        )
        st.session_state["use_sample"] = use_sample
        if not use_sample:
            st.markdown(
                """
                #### این سیستم چه می‌کند؟
                1. فایل را می‌خواند و مشکلات داده را پیدا و اصلاح می‌کند.
                2. معنی هر ستون (مبلغ، تاریخ، مشتری، وضعیت و ...) را تشخیص می‌دهد.
                3. شاخص‌ها، نمودارها و بینش‌های مدیریتی مناسب همان داده را می‌سازد.
                """
            )
            return

    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        filename = uploaded_file.name
    else:
        if not SAMPLE_FILE.exists():
            st.error("فایل نمونه در دسترس نیست.")
            return
        content = SAMPLE_FILE.read_bytes()
        filename = SAMPLE_FILE.name

    try:
        bundle = prepare_analysis(content, filename)
    except ValueError as error:
        st.error(f"❌ {error}")
        return
    except Exception as error:  # noqa: BLE001 - surface unexpected parsing problems
        st.error("❌ پردازش فایل ممکن نشد.")
        st.exception(error)
        return

    filtered = render_sidebar_filters(bundle)

    if filtered.empty:
        st.warning("با فیلترهای فعلی هیچ رکوردی باقی نمانده است.")
        return

    kpi_result = calculate_kpis(filtered, bundle.profile)
    charts = create_charts(filtered, bundle.profile)
    insights = generate_insights(filtered, kpi_result, bundle.profile)

    dashboard_tab, quality_tab, schema_tab, data_tab = st.tabs(
        ["📊 داشبورد", "🔍 کیفیت داده", "🧭 نقشه ستون‌ها", "📋 داده‌ها"]
    )

    with dashboard_tab:
        show_kpis(kpi_result)
        st.divider()
        show_insights(insights)
        st.divider()
        show_charts(charts)

    with quality_tab:
        render_quality_tab(bundle)

    with schema_tab:
        render_schema_tab(bundle)

    with data_tab:
        render_data_tab(bundle, filtered)


main()
