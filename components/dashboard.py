"""Reusable dashboard building blocks."""

import streamlit as st

KPI_COLUMNS = 4
LEVEL_RENDERERS = {
    "positive": st.success,
    "warning": st.warning,
    "info": st.info,
}


def show_header():
    header_html = (
        '<div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; padding: 40px 20px; margin-bottom: 40px; position: relative; overflow: hidden; background: #fefcfb; border-radius: 20px;">'
        '<div style="position: absolute; top: -50px; left: -50px; width: 300px; height: 300px; background: radial-gradient(circle, rgba(235, 120, 100, 0.04) 0%, transparent 70%); z-index: 0;"></div>'
        '<div style="position: absolute; bottom: -50px; right: -50px; width: 400px; height: 400px; background: radial-gradient(circle, rgba(140, 65, 75, 0.03) 0%, transparent 70%); z-index: 0;"></div>'
        '<div style="position: absolute; top: 30px; left: 30px; width: 120px; height: 120px; background-image: radial-gradient(#d4c3b3 1.5px, transparent 1.5px); background-size: 18px 18px; opacity: 0.4; z-index: 0;"></div>'
        '<div style="position: absolute; top: 120px; left: 40%; width: 90px; height: 90px; background-image: radial-gradient(#d4c3b3 1.5px, transparent 1.5px); background-size: 18px 18px; opacity: 0.3; z-index: 0;"></div>'
        '<div style="flex: 1 1 500px; z-index: 2; position: relative; padding-left: 2rem; direction: rtl;">'
        '<div style="display: flex; align-items: center; justify-content: flex-start; gap: 8px; color: #a87b51; font-weight: 700; font-size: 1.05rem; margin-bottom: 15px;">'
        "<span>خوش آمدید!</span>"
        '<span style="font-size: 1.3rem;">🔅</span>'
        "</div>"
        '<h1 style="font-size: 2.7rem; font-weight: 900; color: #1a1a1a; margin: 0 0 20px 0; line-height: 1.4; display: flex; align-items: center; gap: 15px;">'
        "<span>📊</span> پلتفرم تحلیل داده مدیریتی"
        "</h1>"
        '<p style="font-size: 1.25rem; color: #6a5350; line-height: 2; margin: 0; max-width: 650px; font-weight: 500;">'
        "فایل فروش خود را بارگذاری کنید؛ سیستم داده را پاک‌سازی، تحلیل و به "
        '<span style="color: #6a2c35; font-weight: 800;">شاخص، نمودار و پیشنهاد مدیریتی</span> تبدیل می‌کند.'
        "</p>"
        "</div>"
        '<div style="flex: 1 1 350px; position: relative; height: 320px; z-index: 2; display: flex; justify-content: center; align-items: center; margin-top: 20px;">'
        '<div style="position: absolute; width: 260px; height: 260px; background: linear-gradient(135deg, #fdf4eb, #fae8da); border-radius: 50%; left: 50px; top: 20px; z-index: 0;"></div>'
        '<div style="position: absolute; top: 10px; left: 10px; background: #ffffff; padding: 20px; border-radius: 14px; box-shadow: 0 15px 35px rgba(80,45,35,0.06); z-index: 3; width: 150px; border: 1px solid rgba(0,0,0,0.02);">'
        '<div style="display: flex; align-items: flex-end; justify-content: space-between; height: 75px; gap: 8px;">'
        '<div style="width: 22px; height: 45%; background: #f2c99b; border-radius: 4px 4px 0 0;"></div>'
        '<div style="width: 22px; height: 70%; background: #e0927e; border-radius: 4px 4px 0 0;"></div>'
        '<div style="width: 22px; height: 100%; background: #8c414b; border-radius: 4px 4px 0 0;"></div>'
        '<div style="width: 22px; height: 55%; background: #d6a05f; border-radius: 4px 4px 0 0;"></div>'
        "</div>"
        "</div>"
        '<div style="position: absolute; bottom: 10px; right: 20px; background: #ffffff; padding: 22px; border-radius: 16px; box-shadow: 0 20px 40px rgba(80,45,35,0.08); z-index: 4; display: flex; align-items: center; gap: 20px; border: 1px solid rgba(0,0,0,0.02);">'
        '<div style="width: 75px; height: 75px; border-radius: 50%; background: conic-gradient(#8c414b 0% 38%, #f2c99b 38% 65%, #e0927e 65% 100%); position: relative;">'
        '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 35px; height: 35px; background: #ffffff; border-radius: 50%;"></div>'
        "</div>"
        '<div style="direction: rtl; text-align: right;">'
        '<div style="font-size: 0.8rem; color: #a0908d; margin-bottom: 4px; font-weight: 600;">مجموع فروش</div>'
        '<div style="font-size: 1.6rem; font-weight: 900; color: #2c1a17; letter-spacing: 0.5px; direction: ltr;">$ 24,850</div>'
        '<div style="font-size: 0.85rem; color: #059669; margin-top: 6px; font-weight: 700; background: #d1fae5; display: inline-block; padding: 3px 10px; border-radius: 20px; direction: ltr;">+ 12.5% ↗</div>'
        "</div>"
        "</div>"
        '<div style="position: absolute; top: -15px; right: 60px; background: #ffffff; padding: 20px; border-radius: 14px; box-shadow: 0 10px 30px rgba(80,45,35,0.05); z-index: 2; width: 180px; border: 1px solid rgba(0,0,0,0.02);">'
        '<svg viewBox="0 0 100 40" style="width: 100%; height: 40px;">'
        '<path d="M 100 30 Q 80 5 60 20 T 20 10 T 0 25" fill="none" stroke="#e0927e" stroke-width="3" stroke-linecap="round"/>'
        '<circle cx="80" cy="14" r="3.5" fill="#8c414b"/>'
        '<circle cx="40" cy="15" r="3.5" fill="#8c414b"/>'
        '<circle cx="10" cy="17" r="3.5" fill="#8c414b"/>'
        "</svg>"
        '<div style="display: flex; gap: 5px; margin-top: 15px; justify-content: flex-end;">'
        '<div style="height: 4px; width: 30px; background: #f0f0f0; border-radius: 2px;"></div>'
        '<div style="height: 4px; width: 60px; background: #f0f0f0; border-radius: 2px;"></div>'
        "</div>"
        "</div>"
        "</div>"
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)


def show_kpis(kpi_result):
    st.subheader("📌 شاخص‌های کلیدی")

    kpis = getattr(kpi_result, "kpis", [])
    if not kpis:
        st.info("برای این داده شاخص قابل محاسبه‌ای شناسایی نشد.")
        return

    for start in range(0, len(kpis), KPI_COLUMNS):
        row = kpis[start : start + KPI_COLUMNS]
        columns = st.columns(len(row))
        for column, kpi in zip(columns, row):
            with column:
                st.metric(
                    label=kpi.label, value=kpi.display, help=kpi.description
                )


import streamlit as st


import streamlit as st


import streamlit as st

def show_insights(insights):
    st.subheader("💡 یافته‌های کلیدی در یک نگاه")

    if not insights:
        st.info("برای داده فعلی بینشی تولید نشد.")
        return

    # تعریف رنگ‌ها و استایل‌های اختصاصی برای هر سطح
    styles = {
        "info": {
            "bg": "#ffffff",
            "border": "#8c414b",
            "badge": "#f8f4ef",
        },
        "positive": {
            "bg": "#f0fdf4",
            "border": "#16a34a",
            "badge": "#dcfce7",
        },
        "warning": {
            "bg": "#fffbeb",
            "border": "#d97706",
            "badge": "#fef3c7",
        },
    }

    icons = {
        "info": "ℹ️",
        "positive": "📈",
        "warning": "⚠️",
    }

    for insight in insights:
        st_style = styles.get(insight.level, styles["info"])
        icon = icons.get(insight.level, "ℹ️")
        
        content = f"{icon} {insight.text}"
        if insight.evidence:
            content += f"  \n<span dir='ltr' style='background-color: {st_style['badge']}; padding: 2px 8px; border-radius: 4px; display: inline-block; font-weight: bold; color: {st_style['border']};'>`{insight.evidence}`</span>"

        # رندر کارت با استایل رنگی اختصاصی و خط حاشیه رنگی در سمت راست
        st.markdown(f"""
            <div style='
                background-color: {st_style['bg']};
                border-right: 5px solid {st_style['border']};
                border-top: 1px solid #e0d5cb;
                border-left: 1px solid #e0d5cb;
                border-bottom: 1px solid #e0d5cb;
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.02);
                direction: rtl;
                text-align: right;
                font-family: inherit;
            '>
                {content}
            </div>
        """, unsafe_allow_html=True)

def show_charts(charts):
    st.subheader("📈 نمودارهای پیشنهادی")

    if not charts:
        st.info("برای داده فعلی نمودار مناسبی شناسایی نشد.")
        return

    for index in range(0, len(charts), 2):
        row = charts[index : index + 2]
        columns = st.columns(len(row))
        for column, chart in zip(columns, row):
            with column:
                st.plotly_chart(chart.figure, use_container_width=True)
                st.caption(chart.description)