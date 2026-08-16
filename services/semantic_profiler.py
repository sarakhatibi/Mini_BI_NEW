"""Semantic profiling: infer the business meaning of each column.

KPI, chart and insight generation are driven by this profile instead of a
hard coded column list, so the platform also works on unknown datasets.
"""

from dataclasses import dataclass, field

import pandas as pd

from services.text_utils import normalize_text, slugify_column_name

# Name hints are only a signal; statistics decide the final role.
MONEY_HINTS = (
    "amount", "total", "revenue", "sales", "price", "value", "cost", "usd",
    "eur", "irr", "مبلغ", "فروش", "قیمت", "درآمد", "هزینه", "ارزش",
)
QUANTITY_HINTS = ("quantity", "qty", "units", "count", "تعداد", "مقدار", "حجم")
PERCENT_HINTS = ("pct", "percent", "rate", "ratio", "discount", "tax", "درصد", "نرخ", "تخفیف", "مالیات")
CUSTOMER_HINTS = ("customer", "client", "buyer", "account", "مشتری", "خریدار")
PRODUCT_HINTS = ("product", "item", "sku", "service", "کالا", "محصول", "خدمت")
REGION_HINTS = ("region", "province", "state", "city", "country", "استان", "شهر", "منطقه", "کشور")
STATUS_HINTS = ("status", "state", "stage", "وضعیت", "حالت")
SELLER_HINTS = ("salesperson", "seller", "agent", "rep", "فروشنده", "کارشناس", "نماینده")
CHANNEL_HINTS = ("channel", "source", "segment", "کانال", "بخش")
ID_HINTS = ("id", "code", "number", "no", "شناسه", "کد", "شماره")
UNIT_HINTS = ("unit", "uom", "واحد")

NEGATIVE_STATUS_HINTS = (
    "cancel", "return", "refund", "void", "reject", "failed",
    "لغو", "مرجوع", "برگشت", "رد شده", "ابطال",
)
PENDING_STATUS_HINTS = ("pending", "await", "open", "unpaid", "در انتظار", "معوق", "باز")


def _has_hint(column: str, hints) -> bool:
    key = slugify_column_name(column)
    return any(hint in key for hint in hints)


@dataclass
class ColumnProfile:
    name: str
    role: str  # date | measure | percent | category | identifier | text
    subtype: str = ""  # money | quantity | customer | product | region | status | ...
    unique_values: int = 0
    missing: int = 0
    reason: str = ""


@dataclass
class DatasetProfile:
    columns: dict = field(default_factory=dict)
    date_columns: list = field(default_factory=list)
    measure_columns: list = field(default_factory=list)
    percent_columns: list = field(default_factory=list)
    category_columns: list = field(default_factory=list)
    identifier_columns: list = field(default_factory=list)
    text_columns: list = field(default_factory=list)

    money_column: str = ""
    quantity_column: str = ""
    primary_date: str = ""
    customer_column: str = ""
    product_column: str = ""
    region_column: str = ""
    status_column: str = ""
    order_id_column: str = ""
    unit_column: str = ""

    negative_statuses: list = field(default_factory=list)
    pending_statuses: list = field(default_factory=list)

    @property
    def primary_measure(self) -> str:
        return self.money_column or self.quantity_column or (
            self.measure_columns[0] if self.measure_columns else ""
        )

    def dimension_candidates(self) -> list:
        """Categorical columns useful for grouping, most informative first."""
        ordered = [
            column
            for column in (
                self.product_column,
                self.customer_column,
                self.region_column,
                self.status_column,
            )
            if column
        ]
        for column in self.category_columns:
            if column not in ordered:
                ordered.append(column)
        return ordered


def _profile_column(name: str, series: pd.Series) -> ColumnProfile:
    non_null = series.dropna()
    unique_values = int(non_null.nunique())
    missing = int(series.isna().sum())
    rows = max(len(series), 1)

    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnProfile(name, "date", "", unique_values, missing, "نوع داده تاریخ")

    if pd.api.types.is_numeric_dtype(series):
        if _has_hint(name, PERCENT_HINTS):
            return ColumnProfile(name, "percent", "percent", unique_values, missing,
                                 "نام ستون نشان‌دهنده درصد است")
        if _has_hint(name, ID_HINTS) and unique_values > rows * 0.9:
            return ColumnProfile(name, "identifier", "id", unique_values, missing,
                                 "مقادیر یکتا و نام شبیه شناسه")
        if _has_hint(name, MONEY_HINTS):
            return ColumnProfile(name, "measure", "money", unique_values, missing, "سنجه مالی")
        if _has_hint(name, QUANTITY_HINTS):
            return ColumnProfile(name, "measure", "quantity", unique_values, missing, "سنجه مقداری")
        return ColumnProfile(name, "measure", "generic", unique_values, missing, "ستون عددی")

    text = non_null.astype(str)
    average_length = float(text.str.len().mean()) if not text.empty else 0.0

    if _has_hint(name, ID_HINTS) and unique_values > rows * 0.5:
        return ColumnProfile(name, "identifier", "id", unique_values, missing, "مقادیر عمدتاً یکتا")

    if unique_values > rows * 0.5 and average_length > 25:
        return ColumnProfile(name, "text", "free_text", unique_values, missing, "متن آزاد")

    subtype = ""
    for hints, label in (
        (CUSTOMER_HINTS, "customer"),
        (PRODUCT_HINTS, "product"),
        (REGION_HINTS, "region"),
        (STATUS_HINTS, "status"),
        (SELLER_HINTS, "salesperson"),
        (CHANNEL_HINTS, "channel"),
        (UNIT_HINTS, "unit"),
    ):
        if _has_hint(name, hints):
            subtype = label
            break

    if unique_values <= max(50, rows * 0.2):
        return ColumnProfile(name, "category", subtype, unique_values, missing,
                             "تعداد محدود مقدار تکرارشونده")

    return ColumnProfile(name, "text", subtype or "free_text", unique_values, missing, "تنوع بالای مقادیر")


def _detect_status_values(series: pd.Series, hints) -> list:
    values = series.dropna().astype(str).map(normalize_text).unique().tolist()
    return [value for value in values if any(hint in value.lower() for hint in hints)]


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """Infer roles for every column of a cleaned DataFrame."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame.")

    profile = DatasetProfile()

    for column in df.columns:
        column_profile = _profile_column(str(column), df[column])
        profile.columns[column] = column_profile

        if column_profile.role == "date":
            profile.date_columns.append(column)
        elif column_profile.role == "measure":
            profile.measure_columns.append(column)
        elif column_profile.role == "percent":
            profile.percent_columns.append(column)
        elif column_profile.role == "category":
            profile.category_columns.append(column)
        elif column_profile.role == "identifier":
            profile.identifier_columns.append(column)
        else:
            profile.text_columns.append(column)

    # Primary money measure: prefer explicit hints, then the largest total.
    money_candidates = [
        column
        for column in profile.measure_columns
        if profile.columns[column].subtype == "money"
    ]
    if money_candidates:
        profile.money_column = max(
            money_candidates, key=lambda column: float(df[column].abs().sum())
        )
    profile.quantity_column = next(
        (
            column
            for column in profile.measure_columns
            if profile.columns[column].subtype == "quantity"
        ),
        "",
    )

    if profile.date_columns:
        # The date with the widest coverage is the most useful timeline.
        profile.primary_date = max(
            profile.date_columns, key=lambda column: int(df[column].notna().sum())
        )

    def _first_with_subtype(subtype: str) -> str:
        candidates = [
            column
            for column, column_profile in profile.columns.items()
            if column_profile.subtype == subtype
            and column_profile.role in {"category", "text"}
        ]
        if not candidates:
            return ""
        # A readable label beats a technical code column of the same concept.
        readable = [column for column in candidates if not _has_hint(str(column), ID_HINTS)]
        return (readable or candidates)[0]

    profile.customer_column = _first_with_subtype("customer")
    profile.product_column = _first_with_subtype("product")
    profile.region_column = _first_with_subtype("region")
    profile.status_column = _first_with_subtype("status")
    profile.unit_column = _first_with_subtype("unit")

    profile.order_id_column = next(
        (
            column
            for column in profile.identifier_columns
            if _has_hint(str(column), ("order", "invoice", "سفارش", "فاکتور"))
        ),
        profile.identifier_columns[0] if profile.identifier_columns else "",
    )

    if profile.status_column:
        status_series = df[profile.status_column]
        profile.negative_statuses = _detect_status_values(status_series, NEGATIVE_STATUS_HINTS)
        profile.pending_statuses = _detect_status_values(status_series, PENDING_STATUS_HINTS)

    return profile
