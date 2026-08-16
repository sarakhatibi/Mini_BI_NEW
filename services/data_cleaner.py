"""Data cleaning pipeline.

Every transformation is recorded so the user can see (and audit) what the
system decided. Rows are never dropped silently except exact duplicates,
which are reported as well.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher

import pandas as pd

from services.date_utils import parse_dates
from services.numeric_utils import numeric_parse_ratio, parse_numeric_series
from services.text_utils import normalize_column_name, normalize_text

NUMERIC_CONVERSION_THRESHOLD = 0.9
DATE_CONVERSION_THRESHOLD = 0.8
SIMILARITY_THRESHOLD = 0.75
MAX_CATEGORY_CARDINALITY = 200


@dataclass
class CleaningAction:
    """A single, user visible decision taken by the cleaning pipeline."""

    column: str
    action: str
    detail: str
    affected_rows: int = 0

    def as_dict(self) -> dict:
        return {
            "ستون": self.column,
            "اقدام": self.action,
            "توضیح": self.detail,
            "تعداد": self.affected_rows,
        }


@dataclass
class CleaningResult:
    data: pd.DataFrame
    actions: list = field(default_factory=list)
    rejected_values: dict = field(default_factory=dict)
    duplicate_rows_removed: int = 0
    duplicate_id_rows: int = 0

    def actions_frame(self) -> pd.DataFrame:
        if not self.actions:
            return pd.DataFrame(columns=["ستون", "اقدام", "توضیح", "تعداد"])
        return pd.DataFrame([action.as_dict() for action in self.actions])


def _looks_like_date_column(name: str, series: pd.Series) -> bool:
    lowered = str(name).lower()
    if any(keyword in lowered for keyword in ("date", "تاریخ", "زمان", "time")):
        return True

    sample = series.dropna().astype(str).head(200)
    if sample.empty:
        return False
    parsed = parse_dates(sample)
    return float(parsed.notna().mean()) >= 0.95


def _canonicalize_categories(series: pd.Series):
    """Merge near-duplicate labels into their most frequent spelling."""
    
    # 1. تعریف اصلاحات دستی
    common_typos = {
        "اصفهانن": "اصفهان",
        "تهرانـ": "تهران",
    }
    
    # تبدیل مقادیر سری به رشته برای مقایسه و اصلاح دقیق
    series_str = series.astype(str)
    
    # 2. ایجاد مپینگ اولیه از اصلاحات دستی بر اساس مقادیر موجود در ستون
    mapping = {wrong: right for wrong, right in common_typos.items() if wrong in series_str.values}
    
    # 3. اعمال اصلاحات دستی روی مقادیر
    series_str = series_str.replace(common_typos)

    counts = series_str.value_counts()
    if counts.empty or len(counts) > MAX_CATEGORY_CARDINALITY:
        return mapping, series

    canonical = []
    
    # 4. الگوریتم هوشمند برای پیدا کردن سایر شباهت‌ها
    for label in counts.index:
        # اگر مقداری تهی یا nan بود، از آن صرف‌نظر شود
        if label in ("", "nan", "None", "NaN"):
            continue
            
        # اگر قبلاً در لیست دستی اصلاح شده، از آن بگذرد
        if label in mapping.values():
            canonical.append(label)
            continue
            
        match = None
        for candidate in canonical:
            if SequenceMatcher(None, label, candidate).ratio() >= SIMILARITY_THRESHOLD:
                match = candidate
                break
        
        if match is None:
            canonical.append(label)
        else:
            mapping[label] = match

    # ترکیب مپینگ دستی و الگوریتمی برای اعمال نهایی
    full_mapping = {**common_typos, **mapping}
    
    # اعمال نهایی روی سری اصلی بر اساس نوع داده اولیه
    return full_mapping, series.replace(full_mapping)

def clean_dataset(df: pd.DataFrame) -> CleaningResult:
    """Return a typed, normalized copy of ``df`` plus the decisions taken."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame.")

    data = df.copy()
    actions = []
    rejected_values = {}

    # 1. Column names -------------------------------------------------
    renames = {}
    for column in data.columns:
        new_name = normalize_column_name(column)
        if new_name and new_name != str(column):
            renames[column] = new_name
    if renames:
        data = data.rename(columns=renames)
        actions.append(
            CleaningAction(
                column="، ".join(str(key) for key in renames),
                action="اصلاح نام ستون",
                detail="فاصله‌های اضافی و کاراکترهای نامرئی از نام ستون‌ها حذف شد.",
                affected_rows=len(renames),
            )
        )

    # De-duplicate identical column names produced by normalization.
    if data.columns.duplicated().any():
        deduped = []
        seen = {}
        for column in data.columns:
            if column in seen:
                seen[column] += 1
                deduped.append(f"{column}_{seen[column]}")
            else:
                seen[column] = 0
                deduped.append(column)
        data.columns = deduped

    # 2. Empty rows / columns ----------------------------------------
    empty_columns = [column for column in data.columns if data[column].isna().all()]
    if empty_columns:
        data = data.drop(columns=empty_columns)
        actions.append(
            CleaningAction(
                column="، ".join(map(str, empty_columns)),
                action="حذف ستون خالی",
                detail="این ستون‌ها هیچ مقداری نداشتند و از تحلیل کنار گذاشته شدند.",
                affected_rows=len(empty_columns),
            )
        )

    empty_rows = int(data.isna().all(axis=1).sum())
    if empty_rows:
        data = data.dropna(axis=0, how="all")
        actions.append(
            CleaningAction(
                column="—",
                action="حذف ردیف خالی",
                detail="ردیف‌هایی که هیچ مقداری نداشتند حذف شدند.",
                affected_rows=empty_rows,
            )
        )

    # 3. Text normalization ------------------------------------------
    for column in data.columns:
        if not pd.api.types.is_object_dtype(data[column]):
            continue

        original = data[column]
        normalized = original.map(
            lambda value: normalize_text(value) if isinstance(value, str) else value
        )
        normalized = normalized.replace({"": None})

        changed = int((original.fillna("") != normalized.fillna("")).sum())
        data[column] = normalized

        if changed:
            actions.append(
                CleaningAction(
                    column=column,
                    action="یکسان‌سازی متن",
                    detail=(
                        "فاصله‌های اضافی، نیم‌فاصله و حروف عربی/فارسی "
                        "یکسان‌سازی شدند."
                    ),
                    affected_rows=changed,
                )
            )

    # 4. Numeric conversion ------------------------------------------
    for column in data.columns:
        series = data[column]
        if not pd.api.types.is_object_dtype(series):
            continue
        if _looks_like_date_column(column, series):
            continue

        ratio = numeric_parse_ratio(series)
        if ratio < NUMERIC_CONVERSION_THRESHOLD:
            continue

        parsed = parse_numeric_series(series)
        repaired = int(
            (series.notna() & series.astype(str).str.strip().ne("") & parsed.notna()).sum()
        )
        failed_mask = series.notna() & series.astype(str).str.strip().ne("") & parsed.isna()
        failed_values = series[failed_mask].astype(str).unique().tolist()

        data[column] = parsed

        detail = "مقادیر متنی (جداکننده هزار، واحد پول و علامت درصد) به عدد تبدیل شدند."
        if failed_values:
            rejected_values[column] = failed_values[:20]
            detail += f" {len(failed_values)} مقدار غیرقابل تفسیر خالی در نظر گرفته شد."

        actions.append(
            CleaningAction(
                column=column,
                action="تبدیل به عدد",
                detail=detail,
                affected_rows=repaired,
            )
        )

    # 5. Date conversion ---------------------------------------------
    for column in data.columns:
        series = data[column]
        if pd.api.types.is_numeric_dtype(series):
            continue
        if pd.api.types.is_datetime64_any_dtype(series):
            continue
        if not _looks_like_date_column(column, series):
            continue

        parsed = parse_dates(series)
        non_empty = series.notna() & series.astype(str).str.strip().ne("")
        if non_empty.sum() == 0:
            continue

        success_ratio = float(parsed[non_empty].notna().mean())
        if success_ratio < DATE_CONVERSION_THRESHOLD:
            continue

        failed_mask = non_empty & parsed.isna()
        failed_values = series[failed_mask].astype(str).unique().tolist()
        data[column] = parsed

        detail = "قالب‌های مختلف تاریخ (میلادی و شمسی) به یک تاریخ استاندارد تبدیل شدند."
        if failed_values:
            rejected_values.setdefault(column, []).extend(failed_values[:20])
            detail += f" {len(failed_values)} مقدار نامعتبر خالی در نظر گرفته شد."

        actions.append(
            CleaningAction(
                column=column,
                action="تبدیل به تاریخ",
                detail=detail,
                affected_rows=int(parsed.notna().sum()),
            )
        )

# 6. Category consolidation ---------------------------------------
    for column in data.columns:
        series = data[column]
        if not pd.api.types.is_object_dtype(series):
            continue

        # حفظ مقادیر تهی و تبدیل فقط بخش‌های غیرتهی به رشته
        non_null_mask = series.notna()
        if not non_null_mask.any():
            continue

        series_str = series.fillna("").astype(str)
        mapping, merged_str = _canonicalize_categories(series_str)
        if not mapping:
            continue

        # بازگرداندن مقادیر تهی به حالت اولیه NaN
        merged = merged_str.replace("nan", None)
        merged[~non_null_mask] = None

        data[column] = merged
        examples = ", ".join(
            f"«{wrong}» → «{right}»" for wrong, right in list(mapping.items())[:5]
        )
        actions.append(
            CleaningAction(
                column=column,
                action="ادغام مقادیر مشابه",
                detail=f"مقادیر با املای نزدیک یکی شدند: {examples}",
                affected_rows=int(series.isin(mapping).sum()),
            )
        )

    # 7. Duplicates ----------------------------------------------------
    duplicate_rows = int(data.duplicated().sum())
    if duplicate_rows:
        data = data.drop_duplicates()
        actions.append(
            CleaningAction(
                column="—",
                action="حذف رکورد تکراری",
                detail="ردیف‌هایی که در همه ستون‌ها کاملاً یکسان بودند حذف شدند.",
                affected_rows=duplicate_rows,
            )
        )

    duplicate_id_rows = 0
    for column in data.columns:
        lowered = str(column).lower()
        if not (lowered.endswith("_id") or lowered in {"id", "code", "order_id"}):
            continue
        duplicated = int(data[column].dropna().duplicated().sum())
        if duplicated:
            duplicate_id_rows += duplicated
            actions.append(
                CleaningAction(
                    column=column,
                    action="شناسه تکراری (بدون حذف)",
                    detail=(
                        "شناسه‌های تکراری گزارش شدند اما رکوردها حذف نشدند، "
                        "چون ممکن است اصلاحیه یا سفارش چندردیفی باشند."
                    ),
                    affected_rows=duplicated,
                )
            )

    return CleaningResult(
        data=data.reset_index(drop=True),
        actions=actions,
        rejected_values=rejected_values,
        duplicate_rows_removed=duplicate_rows,
        duplicate_id_rows=duplicate_id_rows,
    )
