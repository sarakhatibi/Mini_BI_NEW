"""Management insights: turn the numbers into short, actionable sentences.

Insights are generated from the dataset profile and the KPI context, so a
sentence only appears when the underlying data supports it.
"""

from dataclasses import dataclass

import pandas as pd

from services.kpi_engine import KpiResult, calculate_kpis
from services.semantic_profiler import DatasetProfile, profile_dataset

CONCENTRATION_WARNING = 30.0
HIGH_DISCOUNT = 15.0
OUTLIER_RATIO = 5.0


@dataclass
class Insight:
    """A management level takeaway."""

    text: str
    level: str = "info"  # info | positive | warning
    evidence: str = ""


def _money(value: float) -> str:
    return f"${value:,.0f}" if abs(value) >= 1000 else f"${value:,.2f}"


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _trend_insight(monthly: pd.Series, partial: bool = False) -> list:
    insights = []
    if monthly is None or len(monthly) < 2:
        return insights

    last, previous = monthly.iloc[-1], monthly.iloc[-2]
    if previous:
        change = (last - previous) / abs(previous) * 100
        level = "positive" if change >= 0 else "warning"
        direction = "رشد" if change >= 0 else "افت"
        note = " ماه جاری هنوز کامل نشده و در این مقایسه لحاظ نشده است." if partial else ""
        insights.append(
            Insight(
                f"فروش در {monthly.index[-1]} نسبت به ماه قبل "
                f"{abs(change):,.1f}٪ {direction} داشته است.{note}",
                level,
                f"{_money(float(previous))} → {_money(float(last))}",
            )
        )

    best_month = monthly.idxmax()
    worst_month = monthly.idxmin()
    insights.append(
        Insight(
            f"بهترین ماه {best_month} با {_money(float(monthly.max()))} و ضعیف‌ترین ماه "
            f"{worst_month} با {_money(float(monthly.min()))} بوده است.",
            "info",
        )
    )
    return insights


def generate_insights(df: pd.DataFrame, kpi_result: KpiResult = None,
                      profile: DatasetProfile = None) -> list:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    if profile is None:
        profile = profile_dataset(df)
    if kpi_result is None:
        kpi_result = calculate_kpis(df, profile)

    insights = []
    context = kpi_result.context
    money_column = profile.money_column

    total_sales = kpi_result.get("total_sales")
    if total_sales:
        order_count = kpi_result.get("order_count")
        suffix = f" در {order_count.display} سفارش" if order_count else ""
        insights.append(
            Insight(f"فروش خالص دوره {total_sales.display} است{suffix}.", "info")
        )

    insights.extend(
        _trend_insight(
            context.get("comparable_monthly_sales", context.get("monthly_sales")),
            bool(context.get("partial_last_month")),
        )
    )

    # Concentration risk -------------------------------------------------
    for key, label in (("best_customer", "مشتری"), ("best_product", "محصول")):
        kpi = kpi_result.get(key)
        share = context.get(f"{key}_share")
        if not kpi or share is None:
            continue
        level = "warning" if share >= CONCENTRATION_WARNING else "info"
        message = (
            f"{label} «{kpi.display}» با {_money(kpi.value)} معادل {share:,.1f}٪ از فروش را تشکیل می‌دهد."
        )
        if level == "warning":
            message += " وابستگی درآمد به این یک مورد ریسک محسوب می‌شود."
        insights.append(Insight(message, level))

    # Cancellation / returns ---------------------------------------------
    cancellation = kpi_result.get("cancellation_rate")
    cancelled_value = kpi_result.get("cancelled_value")
    if cancellation:
        level = "warning" if cancellation.value >= 5 else "info"
        evidence = cancelled_value.display if cancelled_value else ""
        insights.append(
            Insight(
                f"{cancellation.display} از رکوردها لغو یا مرجوع شده‌اند و از فروش خالص کنار گذاشته شدند.",
                level,
                evidence,
            )
        )

    # Receivables ----------------------------------------------------------
    pending = kpi_result.get("pending_amount")
    if pending:
        message = f"{pending.display} از فروش هنوز وصول نشده است."
        payment_days = next(
            (
                column
                for column in profile.measure_columns
                if "day" in str(column).lower() or "روز" in str(column)
            ),
            "",
        )
        if payment_days:
            average_days = float(_numeric(df, payment_days).mean())
            message += f" میانگین دوره پرداخت {average_days:,.0f} روز است."
        insights.append(Insight(message, "warning"))

    # Discount pressure -----------------------------------------------------
    discount_column = next(
        (column for column in profile.percent_columns if "discount" in str(column).lower()
         or "تخفیف" in str(column)),
        "",
    )
    if discount_column and money_column:
        discounts = _numeric(df, discount_column)
        average_discount = float(discounts.mean())
        if pd.notna(average_discount) and average_discount > 0:
            high = df[discounts >= HIGH_DISCOUNT]
            level = "warning" if average_discount >= HIGH_DISCOUNT / 2 else "info"
            message = f"میانگین تخفیف {average_discount:,.1f}٪ است."
            if not high.empty:
                message += (
                    f" تعداد سفارش با تخفیف {HIGH_DISCOUNT:.0f}٪ یا بیشتر: {len(high):,}"
                )
            insights.append(Insight(message, level))

    # Outliers ---------------------------------------------------------------
    if money_column:
        values = _numeric(df, money_column).dropna()
        if not values.empty:
            average = float(values.mean())
            largest = float(values.max())
            if average > 0 and largest / average >= OUTLIER_RATIO:
                insights.append(
                    Insight(
                        f"بزرگ‌ترین سفارش ({_money(largest)}) بیش از {largest / average:,.1f} برابر "
                        "میانگین است؛ پیش از تصمیم‌گیری صحت آن بررسی شود.",
                        "warning",
                    )
                )
            negatives = int((values < 0).sum())
            if negatives:
                insights.append(
                    Insight(
                        f"{negatives:,} رکورد مبلغ منفی دارد که معمولاً نشانه برگشت از فروش یا خطای ثبت است.",
                        "warning",
                    )
                )

    # Region / channel opportunity --------------------------------------------
    if money_column and profile.region_column:
        # Regional comparison should ignore cancelled/returned rows, like the KPIs.
        active = context.get("active_rows")
        if not isinstance(active, pd.DataFrame) or active.empty:
            active = df
        grouped = (
            active.assign(_value=_numeric(active, money_column))
            .dropna(subset=["_value"])
            .groupby(profile.region_column)["_value"]
            .sum()
            .sort_values(ascending=False)
        )
        if len(grouped) >= 2:
            insights.append(
                Insight(
                    f'بیشترین فروش از «{grouped.index[0]}» (<span dir="ltr">{_money(float(grouped.iloc[0]))}</span>) و '
                    f'کمترین فروش از «{grouped.index[-1]}» (<span dir="ltr">{_money(float(grouped.iloc[-1]))}</span>) به دست آمده است.',
                    "info",
                )
            )

    insights.append(
        Insight(f"این تحلیل بر پایه {len(df):,} رکورد پس از پاک‌سازی و فیلترهای فعال است.", "info")
    )

    return insights
