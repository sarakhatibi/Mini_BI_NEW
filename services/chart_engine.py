"""Automatic visualization selection based on the dataset profile."""

from dataclasses import dataclass

import pandas as pd
import plotly.express as px

from services.semantic_profiler import DatasetProfile, profile_dataset

TOP_N = 10
MAX_DONUT_SLICES = 8


@dataclass
class ChartSpec:
    """A chart together with the reason it was chosen."""

    key: str
    title: str
    description: str
    figure: object


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _active_rows(df: pd.DataFrame, profile: DatasetProfile) -> pd.DataFrame:
    if not profile.status_column or not profile.negative_statuses:
        return df
    return df[~df[profile.status_column].isin(profile.negative_statuses)]


def _style(figure):
    figure.update_layout(
        margin=dict(l=10, r=10, t=60, b=10),
        title_x=0.5,
        legend_title_text="",
        hoverlabel=dict(namelength=-1),
    )
    return figure


def _trend_chart(df: pd.DataFrame, profile: DatasetProfile, measure: str):
    date_column = profile.primary_date
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(df[date_column], errors="coerce"),
            "value": _numeric(df, measure),
        }
    ).dropna()

    if frame.empty:
        return None

    span_days = (frame["date"].max() - frame["date"].min()).days
    if span_days > 730:
        rule, label = "QS", "فصل"
    elif span_days > 90:
        rule, label = "MS", "ماه"
    elif span_days > 14:
        rule, label = "W", "هفته"
    else:
        rule, label = "D", "روز"

    grouped = frame.set_index("date").resample(rule)["value"].sum().reset_index()
    if len(grouped) < 2:
        return None

    figure = px.line(
        grouped,
        x="date",
        y="value",
        markers=True,
        title=f"روند {measure} بر حسب {label}",
        labels={"date": "زمان", "value": measure},
    )
    figure.update_traces(line=dict(width=3))
    return ChartSpec(
        "trend",
        f"روند {measure}",
        f"مجموع {measure} در هر {label}؛ برای دیدن رشد یا افت در طول زمان.",
        _style(figure),
    )


def _top_categories_chart(df: pd.DataFrame, dimension: str, measure: str):
    grouped = (
        df.assign(_value=_numeric(df, measure))
        .dropna(subset=["_value"])
        .groupby(dimension, as_index=False)["_value"]
        .sum()
        .sort_values("_value", ascending=False)
        .head(TOP_N)
    )
    if grouped.empty:
        return None

    figure = px.bar(
        grouped.sort_values("_value"),
        x="_value",
        y=dimension,
        orientation="h",
        text_auto=".2s",
        title=f"{TOP_N} مورد برتر بر اساس {measure} در {dimension}",
        labels={"_value": measure, dimension: dimension},
    )
    return ChartSpec(
        f"top_{dimension}",
        f"برترین‌های {dimension}",
        f"سهم هر {dimension} از {measure}؛ برای شناسایی تمرکز فروش.",
        _style(figure),
    )


def _share_chart(df: pd.DataFrame, dimension: str, measure: str):
    grouped = (
        df.assign(_value=_numeric(df, measure))
        .dropna(subset=["_value"])
        .groupby(dimension, as_index=False)["_value"]
        .sum()
        .sort_values("_value", ascending=False)
    )
    grouped = grouped[grouped["_value"] > 0]
    if grouped.empty or len(grouped) < 2:
        return None

    if len(grouped) > MAX_DONUT_SLICES:
        head = grouped.head(MAX_DONUT_SLICES - 1)
        others = pd.DataFrame(
            {dimension: ["سایر"], "_value": [grouped["_value"][MAX_DONUT_SLICES - 1:].sum()]}
        )
        grouped = pd.concat([head, others], ignore_index=True)

    figure = px.pie(
        grouped,
        names=dimension,
        values="_value",
        hole=0.45,
        title=f"سهم {dimension} از {measure}",
    )
    figure.update_traces(textposition="inside", textinfo="percent+label")
    return ChartSpec(
        f"share_{dimension}",
        f"سهم {dimension}",
        f"درصد مشارکت هر {dimension} در {measure}.",
        _style(figure),
    )


def _distribution_chart(df: pd.DataFrame, measure: str):
    values = _numeric(df, measure).dropna()
    if values.empty or values.nunique() < 5:
        return None

    figure = px.histogram(
        values.to_frame(measure),
        x=measure,
        nbins=40,
        title=f"توزیع {measure}",
    )
    return ChartSpec(
        "distribution",
        f"توزیع {measure}",
        "پراکندگی مقادیر؛ برای تشخیص سفارش‌های خیلی بزرگ یا خیلی کوچک.",
        _style(figure),
    )


def _status_chart(df: pd.DataFrame, profile: DatasetProfile):
    column = profile.status_column
    counts = df[column].dropna().value_counts().reset_index()
    counts.columns = [column, "count"]
    if counts.empty:
        return None

    figure = px.bar(
        counts,
        x=column,
        y="count",
        text_auto=True,
        title=f"تعداد رکورد در هر {column}",
        labels={"count": "تعداد رکورد"},
    )
    return ChartSpec(
        "status",
        f"وضعیت {column}",
        "ترکیب وضعیت سفارش‌ها؛ سهم لغو و مرجوعی را نشان می‌دهد.",
        _style(figure),
    )


def create_charts(df: pd.DataFrame, profile: DatasetProfile = None) -> list:
    """Choose a small set of charts that match the meaning of the data."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    if profile is None:
        profile = profile_dataset(df)

    measure = profile.primary_measure
    if not measure:
        return []

    active = _active_rows(df, profile)
    charts = []

    if profile.primary_date:
        chart = _trend_chart(active, profile, measure)
        if chart:
            charts.append(chart)

    dimensions = [
        column
        for column in profile.dimension_candidates()
        if column != profile.status_column
    ]

    for dimension in dimensions[:2]:
        chart = _top_categories_chart(active, dimension, measure)
        if chart:
            charts.append(chart)

    share_dimension = next(
        (
            column
            for column in dimensions
            if 1 < df[column].dropna().nunique() <= 12
        ),
        None,
    )
    if share_dimension:
        chart = _share_chart(active, share_dimension, measure)
        if chart:
            charts.append(chart)

    if profile.status_column:
        chart = _status_chart(df, profile)
        if chart:
            charts.append(chart)

    chart = _distribution_chart(active, measure)
    if chart:
        charts.append(chart)

    return charts
