"""KPI detection driven by the semantic profile of the dataset.

Nothing here is bound to a specific file: the engine asks the profile which
column plays which business role and only produces the KPIs that the data
can actually support.
"""

from dataclasses import dataclass, field

import pandas as pd

from services.semantic_profiler import DatasetProfile, profile_dataset


@dataclass
class Kpi:
    key: str
    label: str
    value: float
    display: str
    description: str = ""


@dataclass
class KpiResult:
    kpis: list = field(default_factory=list)
    context: dict = field(default_factory=dict)

    def get(self, key: str):
        return next((kpi for kpi in self.kpis if kpi.key == key), None)

    def as_dict(self) -> dict:
        return {kpi.key: kpi.value for kpi in self.kpis}


def _money(value: float) -> str:
    return f"${value:,.0f}" if abs(value) >= 1000 else f"${value:,.2f}"


def _valid_measure(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce").dropna()


def _effective_rows(df: pd.DataFrame, profile: DatasetProfile) -> pd.DataFrame:
    """Rows that represent realised business, i.e. not cancelled or returned."""
    if not profile.status_column or not profile.negative_statuses:
        return df
    return df[~df[profile.status_column].isin(profile.negative_statuses)]


def calculate_kpis(df: pd.DataFrame, profile: DatasetProfile = None) -> KpiResult:
    result = KpiResult()

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return result

    if profile is None:
        profile = profile_dataset(df)

    result.context["profile"] = profile

    result.kpis.append(
        Kpi("total_rows", "تعداد رکورد", float(len(df)), f"{len(df):,}", "تعداد ردیف‌های داده پس از فیلترها")
    )

    active = _effective_rows(df, profile)
    excluded = len(df) - len(active)
    result.context["active_rows"] = active
    result.context["excluded_rows"] = excluded
    result.context["negative_statuses"] = profile.negative_statuses

    # --- Orders -------------------------------------------------------
    if profile.order_id_column:
        orders = int(df[profile.order_id_column].dropna().nunique())
        result.kpis.append(
            Kpi("order_count", "تعداد سفارش", float(orders), f"{orders:,}",
                f"بر اساس مقادیر یکتای ستون «{profile.order_id_column}»")
        )

    money_column = profile.money_column
    if money_column:
        gross = _valid_measure(df, money_column)
        net = _valid_measure(active, money_column)

        if not net.empty:
            total = float(net.sum())
            result.kpis.append(
                Kpi("total_sales", "فروش خالص", total, _money(total),
                    (f"مجموع «{money_column}» بدون رکوردهای "
                     f"{'، '.join(profile.negative_statuses)}" if excluded
                     else f"مجموع ستون «{money_column}»"))
            )

            average = float(net.mean())
            result.kpis.append(
                Kpi("average_order_value", "میانگین ارزش سفارش", average, _money(average),
                    "میانگین مبلغ هر رکورد فروش")
            )

            median = float(net.median())
            result.kpis.append(
                Kpi("median_sale", "میانه فروش", median, _money(median),
                    "نصف سفارش‌ها کمتر از این مبلغ هستند")
            )

            largest = float(net.max())
            result.kpis.append(
                Kpi("largest_sale", "بزرگ‌ترین سفارش", largest, _money(largest), "بیشترین مبلغ یک رکورد")
            )

        if excluded and not gross.empty:
            lost = float(gross.sum() - (net.sum() if not net.empty else 0.0))
            result.kpis.append(
                Kpi("cancelled_value", "مبلغ لغو/مرجوعی", lost, _money(lost),
                    f"{excluded:,} رکورد با وضعیت لغو یا مرجوعی از فروش خالص کنار گذاشته شد")
            )

    # --- Quantity (only when the unit is consistent) --------------------
    if profile.quantity_column:
        units = (
            df[profile.unit_column].dropna().nunique() if profile.unit_column else 1
        )
        quantity = _valid_measure(active, profile.quantity_column)
        if not quantity.empty and units <= 1:
            total_quantity = float(quantity.sum())
            result.kpis.append(
                Kpi("total_quantity", "مجموع مقدار", total_quantity, f"{total_quantity:,.0f}",
                    f"مجموع ستون «{profile.quantity_column}»")
            )
        elif not quantity.empty:
            result.context["quantity_units"] = int(units)

    # --- Customers ------------------------------------------------------
    if profile.customer_column:
        customers = df[profile.customer_column].dropna().astype(str)
        customers = customers[customers.str.strip() != ""]
        if not customers.empty:
            unique_customers = int(customers.nunique())
            result.kpis.append(
                Kpi("unique_customers", "تعداد مشتری", float(unique_customers),
                    f"{unique_customers:,}", "تعداد مشتریان یکتا پس از یکسان‌سازی نام‌ها")
            )

    # --- Best customer / product ---------------------------------------
    if money_column:
        for column, key, label in (
            (profile.customer_column, "best_customer", "بهترین مشتری"),
            (profile.product_column, "best_product", "پرفروش‌ترین محصول"),
            (profile.region_column, "best_region", "بهترین منطقه"),
        ):
            if not column or column not in active.columns:
                continue
            grouped = (
                active.assign(_value=pd.to_numeric(active[money_column], errors="coerce"))
                .dropna(subset=["_value"])
                .groupby(column)["_value"]
                .sum()
                .sort_values(ascending=False)
            )
            if grouped.empty:
                continue
            top_name = str(grouped.index[0])
            top_value = float(grouped.iloc[0])
            share = top_value / float(grouped.sum()) * 100 if grouped.sum() else 0.0
            result.kpis.append(
                Kpi(key, label, top_value, top_name,
                    f"{_money(top_value)} معادل {share:,.1f}٪ از کل فروش")
            )
            result.context[f"{key}_share"] = share
            result.context[f"{key}_table"] = grouped

    # --- Cancellation rate ----------------------------------------------
    if profile.status_column and profile.negative_statuses:
        rate = excluded / len(df) * 100 if len(df) else 0.0
        result.kpis.append(
            Kpi("cancellation_rate", "نرخ لغو و مرجوعی", rate, f"{rate:,.1f}٪",
                f"سهم رکوردهای {'، '.join(profile.negative_statuses)} از کل رکوردها")
        )

    # --- Outstanding receivables -----------------------------------------
    if profile.status_column and profile.pending_statuses and money_column:
        pending = df[df[profile.status_column].isin(profile.pending_statuses)]
        pending_value = float(pd.to_numeric(pending[money_column], errors="coerce").sum())
        if pending_value:
            result.kpis.append(
                Kpi("pending_amount", "مطالبات وصول‌نشده", pending_value, _money(pending_value),
                    f"مجموع مبلغ رکوردهای {'، '.join(profile.pending_statuses)}")
            )

    # --- Month over month growth ------------------------------------------
    if profile.primary_date and money_column:
        timeline = (
            active.assign(
                _period=pd.to_datetime(active[profile.primary_date], errors="coerce").dt.to_period("M"),
                _value=pd.to_numeric(active[money_column], errors="coerce"),
            )
            .dropna(subset=["_period", "_value"])
            .groupby("_period")["_value"]
            .sum()
            .sort_index()
        )
        result.context["monthly_sales"] = timeline

        # A month that is still running would fake a collapse in sales.
        dates = pd.to_datetime(active[profile.primary_date], errors="coerce").dropna()
        partial = bool(
            len(timeline)
            and not dates.empty
            and dates.max() < timeline.index[-1].to_timestamp(how="end").normalize()
        )
        result.context["partial_last_month"] = partial
        comparable = timeline.iloc[:-1] if partial else timeline
        result.context["comparable_monthly_sales"] = comparable

        if len(comparable) >= 2 and comparable.iloc[-2] != 0:
            growth = (comparable.iloc[-1] - comparable.iloc[-2]) / abs(comparable.iloc[-2]) * 100
            note = " (ماه جاری ناقص است و کنار گذاشته شد)" if partial else ""
            result.kpis.append(
                Kpi("mom_growth", "رشد ماهانه", float(growth), f"{growth:,.1f}٪",
                    f"مقایسه {comparable.index[-1]} با {comparable.index[-2]}{note}")
            )

    # --- Generic fallback --------------------------------------------------
    if not money_column and profile.measure_columns:
        column = profile.measure_columns[0]
        values = _valid_measure(df, column)
        if not values.empty:
            result.kpis.append(
                Kpi("primary_measure_total", f"مجموع {column}", float(values.sum()),
                    f"{values.sum():,.2f}", "مهم‌ترین ستون عددی شناسایی‌شده")
            )
            result.kpis.append(
                Kpi("primary_measure_average", f"میانگین {column}", float(values.mean()),
                    f"{values.mean():,.2f}", "میانگین همان ستون")
            )

    return result
