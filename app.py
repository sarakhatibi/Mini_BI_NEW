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
    
    # نمایش زیبا و خوانای تعداد رکوردهای انتخاب‌شده
    delta_count = len(filtered) - len(data)
    delta_str = f"{delta_count:,}" if delta_count != 0 else "بدون فیلتر"
    
    st.sidebar.markdown(
        f"""
        <div style="background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 14px; text-align: center; margin-top: 10px;">
            <div style="color: #e2e8f0; font-size: 0.85rem; margin-bottom: 4px; font-family: 'Vazirmatn', sans-serif;">رکوردهای انتخاب‌شده</div>
            <div style="color: #ffffff; font-size: 1.6rem; font-weight: 800; font-family: 'Vazirmatn', sans-serif;">{len(filtered):,}</div>
            <div style="color: #cbd5e1; font-size: 0.8rem; margin-top: 2px; font-family: 'Vazirmatn', sans-serif;">تغییر: {delta_str}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    return filtered

def inject_custom_uploader_css():
    """تزریق استایل برای بزرگ‌سازی تب‌ها، یکدست‌سازی فونت و خوانایی سایدبار."""
    st.markdown(
        """
        <style>
        @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
        
        /* ۱. فونت پایه تمام صفحه */
        * {
            font-family: 'Vazirmatn', sans-serif !important;
        }

        /* ۲. استایل کامل و اجباری برای بزرگ‌سازی تب‌ها (st.tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px !important;
            direction: rtl !important;
            padding-bottom: 8px !important;
        }

        .stTabs [data-baseweb="tab"] {
            height: 52px !important;
            padding: 8px 24px !important;
            background-color: #ffffff !important;
            border-radius: 12px 12px 0px 0px !important;
            border: 1px solid #e0d5cb !important;
            border-bottom: none !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04) !important;
            transition: all 0.25s ease !important;
        }

        /* بزرگ‌کردن فونت تمام متون، آیکون‌ها و تگ‌های درون تب */
        .stTabs [data-baseweb="tab"] *,
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {
            font-size: 1.25rem !important;
            font-weight: 800 !important;
            color: #5c3a31 !important;
            line-height: 1.6 !important;
        }

        /* حالت هوور (شناور شدن موس روی تب) */
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #fff6f3 !important;
            transform: translateY(-3px) !important;
        }

        .stTabs [data-baseweb="tab"]:hover * {
            color: #8c414b !important;
        }

        /* تب فعال (انتخاب شده) */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #ffffff !important;
            border-top: 4px solid #8c414b !important;
            box-shadow: 0 -4px 12px rgba(140, 65, 75, 0.15) !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] * {
            color: #8c414b !important;
        }

        /* خط زیرین کل تب‌ها */
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #8c414b !important;
            height: 3px !important;
        }

        /* ۳. متون و عناوین سایدبار */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown {
            color: #ffffff !important;
        }

        /* ۴. اصلاح ورودی تاریخ و باکس‌های سایدبار */
        [data-testid="stSidebar"] input[type="text"],
        [data-testid="stSidebar"] div[data-baseweb="input"] input {
            color: #0f172a !important;
            background-color: #ffffff !important;
            font-weight: 600 !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="input"] {
            background-color: #ffffff !important;
            border-radius: 8px !important;
            border: 1px solid #cbd5e1 !important;
        }

        /* ۵. اصلاح باکس‌های انتخابی (Multiselect) */
        [data-testid="stSidebar"] div[data-baseweb="select"] {
            background-color: #ffffff !important;
            border-radius: 8px !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #0f172a !important;
        }

        /* ۶. اصلاح دکمه بازنشانی فیلترها */
        [data-testid="stSidebar"] button {
            background-color: rgba(255, 255, 255, 0.15) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }

        [data-testid="stSidebar"] button:hover {
            background-color: rgba(255, 255, 255, 0.25) !important;
            border-color: #ffffff !important;
        }

        /* ۷. اصلاح باکس Expander فیلترهای عددی */
        [data-testid="stSidebar"] .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }

        /* ۸. مخفی کردن کدهای خام آیکون بالای سایدبار */
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stSidebarExpandButton"] span {
            display: none !important;
        }

        /* ۹. استایل کادر آپلود */
        div[data-testid="stFileUploader"] {
            background-color: #ffffff !important;
            border: 2px dashed #e0927e !important;
            border-radius: 16px !important;
            padding: 12px !important;
        }

        div[data-testid="stFileUploader"] button {
            background: linear-gradient(135deg, #8c414b 0%, #6a2c35 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
        }

        /* ۱۰. کارت‌های سایدبار */
        .sidebar-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            direction: rtl;
            text-align: center !important;
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
def render_sidebar_landing():
    """رندر سایدبار با متن‌های کاملاً وسط‌چین شده."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-card">
                <div style="color: #4ade80 !important; font-weight: bold; font-size: 0.95rem; margin-bottom: 6px; text-align: center;">
                    ● سیستم آماده دریافت داده
                </div>
                <div style="color: #ffffff !important; font-size: 0.85rem; line-height: 1.6; text-align: center;">
                    فایل اکسل یا CSV خود را آپلود کنید تا فیلترهای هوشمند فعال شوند.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-card">
                <div style="color: #ffffff !important; font-weight: bold; font-size: 0.95rem; margin-bottom: 10px; text-align: center;">
                    🚀 مراحل شروع کار
                </div>
                <div style="color: #ffffff !important; font-size: 0.85rem; line-height: 1.8; text-align: center;">
                    <b>۱.</b> انتخاب یا کشیدن فایل در کادر<br>
                    <b>۲.</b> پاک‌سازی خودکار و تشخیص ستون‌ها<br>
                    <b>۳.</b> مشاهده شاخص‌ها و اعمال فیلترها
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-card">
                <div style="color: #ffffff !important; font-weight: bold; font-size: 0.95rem; margin-bottom: 10px; text-align: center;">
                    📊 ستون‌های پیشنهادی
                </div>
                <div style="color: #ffffff !important; font-size: 0.85rem; line-height: 1.9; text-align: center;">
                    • <b>تاریخ:</b> روز / ماه / سال<br>
                    • <b>مبلغ:</b> عدد فروش یا درآمد<br>
                    • <b>مشتری / کالا:</b> نام خریدار یا محصول
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_landing_hero():
    """کارت گرافیکی فوق‌العاده شیک برای راهنمای اولیه کاربر."""
    hero_html = (
        '<div style="background: linear-gradient(135deg, #ffffff 0%, #fdfbf7 100%); border-radius: 20px; padding: 35px 30px; margin: 25px 0 35px 0; border: 1px solid rgba(220,200,185,0.3); box-shadow: 0 12px 30px rgba(0,0,0,0.03); position: relative; overflow: hidden; direction: rtl; text-align: right;">'
        '<div style="position: absolute; top: -30px; left: -30px; width: 180px; height: 180px; background: radial-gradient(circle, rgba(224,146,126,0.1) 0%, transparent 70%); border-radius: 50%;"></div>'
        '<div style="position: absolute; bottom: -40px; right: -40px; width: 220px; height: 220px; background: radial-gradient(circle, rgba(140,65,75,0.06) 0%, transparent 70%); border-radius: 50%;"></div>'
        '<div style="margin-bottom: 25px; position: relative; z-index: 2;">'
        '<span style="background: rgba(168,123,81,0.1); color: #8c414b; font-size: 0.85rem; font-weight: 800; padding: 6px 14px; border-radius: 30px; display: inline-block; margin-bottom: 12px;">💡 راهنمای سریع</span>'
        '<h3 style="font-size: 1.6rem; font-weight: 900; color: #1a1a1a; margin: 0 0 8px 0; line-height: 1.4;">این سیستم هوشمند چگونه کار می‌کند؟</h3>'
        '<p style="color: #6a5350; font-size: 1.05rem; margin: 0; font-weight: 500;">تنها با چند کلیک، فایل اکسل یا CSV خام خود را به یک داشبورد مدیریتی کامل تبدیل کنید:</p>'
        "</div>"
        '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; position: relative; z-index: 2;">'
        '<div style="background: #ffffff; padding: 20px; border-radius: 16px; border: 1px solid #f0e8e0; box-shadow: 0 4px 15px rgba(0,0,0,0.02); transition: transform 0.2s;">'
        '<div style="font-size: 1.8rem; margin-bottom: 10px;">🧹</div>'
        '<div style="font-size: 1.1rem; font-weight: 800; color: #2c1a17; margin-bottom: 6px;">۱. پاک‌سازی خودکار</div>'
        '<div style="font-size: 0.92rem; color: #7a6865; line-height: 1.6;">شناسایی خطاهای داده، مقادیر خالی و اصلاح فرمت‌های نادرست بدون نیاز به مداخله شما.</div>'
        "</div>"
        '<div style="background: #ffffff; padding: 20px; border-radius: 16px; border: 1px solid #f0e8e0; box-shadow: 0 4px 15px rgba(0,0,0,0.02); transition: transform 0.2s;">'
        '<div style="font-size: 1.8rem; margin-bottom: 10px;">🧭</div>'
        '<div style="font-size: 1.1rem; font-weight: 800; color: #2c1a17; margin-bottom: 6px;">۲. درک هوشمند ستون‌ها</div>'
        '<div style="font-size: 0.92rem; color: #7a6865; line-height: 1.6;">تشخیص خودکار ستون‌های فروش، تاریخ، مشتری، محصول و وضعیت برای تحلیل دقیق.</div>'
        "</div>"
        '<div style="background: #ffffff; padding: 20px; border-radius: 16px; border: 1px solid #f0e8e0; box-shadow: 0 4px 15px rgba(0,0,0,0.02); transition: transform 0.2s;">'
        '<div style="font-size: 1.8rem; margin-bottom: 10px;">📊</div>'
        '<div style="font-size: 1.1rem; font-weight: 800; color: #2c1a17; margin-bottom: 6px;">۳. تولید داشبورد و بینش</div>'
        '<div style="font-size: 0.92rem; color: #7a6865; line-height: 1.6;">محاسبه شاخص‌های کلیدی (KPI)، رسم نمودارهای کاربردی و ارائه پیشنهادهای مدیریتی.</div>'
        "</div>"
        "</div>"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)


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
    inject_style(theme="muted")
    inject_custom_uploader_css()

    show_header()

    st.markdown(
        """
        <div style="direction: rtl; text-align: right; margin-bottom: 12px;">
            <span style="font-size: 1.4rem; font-weight: 900; color: #2c1a17;">📁 بارگذاری فایل داده</span>
            <span style="font-size: 1.05rem; color: #8c736c; margin-right: 10px; font-weight: 600;">(فرمت‌های پشتیبانی شده: CSV, XLSX)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "لیبل مخفی",
        type=["csv", "xlsx", "xls"],
        help="فایل فروش خود را بارگذاری کنید؛ نیازی به تمیز کردن قبلی نیست.",
        label_visibility="collapsed",
    )

    use_sample = False
    if uploaded_file is None:
        st.write("")
        st.info("👆 فایل خود را در باکس بالا بکشید یا برای آزمایش، داده نمونه را ببینید:")
        use_sample = st.button(
            "📈 نمایش با داده نمونه", type="primary"
        ) or st.session_state.get("use_sample", False)
        st.session_state["use_sample"] = use_sample

        if not use_sample:
            render_sidebar_landing()
            render_landing_hero()
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
    except Exception as error:  # noqa: BLE001
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


if __name__ == "__main__":
    main()