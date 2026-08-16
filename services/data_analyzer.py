"""Dataset profiling and data quality assessment.

``analyze_dataset`` describes the structure of a dataset; ``assess_quality``
scores it and lists the concrete problems found, including the ones the
cleaning pipeline already repaired.
"""

import pandas as pd

from services.numeric_utils import numeric_parse_ratio, parse_numeric_series
from services.semantic_profiler import profile_dataset

ROLE_LABELS = {
    "date": "تاریخ",
    "measure": "عددی",
    "percent": "درصد",
    "category": "دسته‌بندی",
    "identifier": "شناسه",
    "text": "متن",
}

SUBTYPE_LABELS = {
    "money": "مبلغ",
    "quantity": "مقدار",
    "customer": "مشتری",
    "product": "محصول",
    "region": "منطقه",
    "status": "وضعیت",
    "salesperson": "فروشنده",
    "channel": "کانال",
    "unit": "واحد",
    "id": "شناسه",
}

OUTLIER_IQR_FACTOR = 3.0


def analyze_dataset(df: pd.DataFrame, profile=None) -> dict:
    """Return a structural description of the dataset."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame.")
    if df.empty or len(df.columns) == 0:
        raise ValueError("Dataset is empty.")

    if profile is None:
        profile = profile_dataset(df)

    missing_values = df.isna().sum()
    missing_values = missing_values[missing_values > 0]

    column_summary = []
    for column in df.columns:
        column_profile = profile.columns[column]
        non_null = df[column].dropna()
        sample = non_null.iloc[0] if not non_null.empty else ""
        column_summary.append(
            {
                "ستون": column,
                "نقش": ROLE_LABELS.get(column_profile.role, column_profile.role),
                "معنی تجاری": SUBTYPE_LABELS.get(column_profile.subtype, "—"),
                "مقادیر یکتا": column_profile.unique_values,
                "خالی": column_profile.missing,
                "نمونه": str(sample)[:40],
            }
        )

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "missing_values": missing_values.to_dict(),
        "total_missing": int(missing_values.sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "data_types": df.dtypes.astype(str).to_dict(),
        "numeric_columns": profile.measure_columns + profile.percent_columns,
        "text_columns": profile.category_columns + profile.text_columns,
        "date_columns": profile.date_columns,
        "identifier_columns": profile.identifier_columns,
        "column_summary": column_summary,
        "profile": profile,
    }


def _detect_outliers(series: pd.Series) -> int:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if len(values) < 20:
        return 0
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return 0
    lower = q1 - OUTLIER_IQR_FACTOR * iqr
    upper = q3 + OUTLIER_IQR_FACTOR * iqr
    return int(((values < lower) | (values > upper)).sum())


def assess_quality(raw_df: pd.DataFrame, clean_df: pd.DataFrame, cleaning_result=None,
                   profile=None) -> dict:
    """Score data quality and list the issues found in the raw file."""
    if profile is None:
        profile = profile_dataset(clean_df)

    issues = []
    rows = max(len(raw_df), 1)

    def _missing_severity(ratio: float) -> str:
        if ratio > 0.2:
            return "بالا"
        return "متوسط" if ratio > 0.01 else "کم"

    # Missing values ---------------------------------------------------
    missing_by_column = clean_df.isna().sum()
    total_missing = int(missing_by_column.sum())
    total_cells = max(clean_df.size, 1)
    for column, count in missing_by_column[missing_by_column > 0].items():
        issues.append(
            {
                "ستون": column,
                "نوع مشکل": "مقدار خالی",
                "شدت": _missing_severity(count / rows),
                "توضیح": f"{int(count):,} مقدار خالی ({count / rows * 100:,.1f}٪ رکوردها)",
            }
        )

    # Duplicates --------------------------------------------------------
    duplicate_rows = (
        cleaning_result.duplicate_rows_removed if cleaning_result else int(raw_df.duplicated().sum())
    )
    if duplicate_rows:
        issues.append(
            {
                "ستون": "—",
                "نوع مشکل": "رکورد تکراری",
                "شدت": "بالا",
                "توضیح": f"{duplicate_rows:,} رکورد کاملاً تکراری شناسایی و حذف شد",
            }
        )

    if cleaning_result and cleaning_result.duplicate_id_rows:
        issues.append(
            {
                "ستون": profile.order_id_column or "شناسه",
                "نوع مشکل": "شناسه تکراری",
                "شدت": "متوسط",
                "توضیح": (
                    f"{cleaning_result.duplicate_id_rows:,} شناسه تکراری است؛ "
                    "رکوردها حذف نشدند و نیاز به بررسی دارند"
                ),
            }
        )

    # Mixed / repaired formats -------------------------------------------
    for column in raw_df.columns:
        series = raw_df[column]
        if not pd.api.types.is_object_dtype(series):
            continue
        if column not in clean_df.columns or not pd.api.types.is_numeric_dtype(clean_df[column]):
            # A categorical column such as "30 روزه" is not a broken number.
            continue
        ratio = numeric_parse_ratio(series)
        if 0.5 <= ratio < 1:
            non_null = series.dropna()
            parsed = parse_numeric_series(non_null)
            examples = non_null[parsed.isna()].astype(str).head(3).tolist()
            if not examples:
                continue
            issues.append(
                {
                    "ستون": column,
                    "نوع مشکل": "قالب عددی ناسازگار",
                    "شدت": "متوسط",
                    "توضیح": f"مقادیری مانند {examples} در ستون عددی ذخیره شده‌اند",
                }
            )

    # Rejected values ------------------------------------------------------
    if cleaning_result:
        for column, values in cleaning_result.rejected_values.items():
            issues.append(
                {
                    "ستون": column,
                    "نوع مشکل": "مقدار غیرقابل تفسیر",
                    "شدت": "بالا",
                    "توضیح": f"مقادیری مانند {values[:3]} قابل تبدیل نبودند و خالی در نظر گرفته شدند",
                }
            )

    # Business rule violations ---------------------------------------------
    for column in profile.measure_columns:
        values = pd.to_numeric(clean_df[column], errors="coerce").dropna()
        if values.empty:
            continue
        negatives = int((values < 0).sum())
        if negatives:
            issues.append(
                {
                    "ستون": column,
                    "نوع مشکل": "مقدار منفی",
                    "شدت": "بالا",
                    "توضیح": f"{negatives:,} مقدار منفی در ستونی که انتظار عدد مثبت می‌رود",
                }
            )
        outliers = _detect_outliers(values)
        if outliers and outliers / len(values) <= 0.05:
            issues.append(
                {
                    "ستون": column,
                    "نوع مشکل": "مقدار پرت",
                    "شدت": "متوسط",
                    "توضیح": f"{outliers:,} مقدار بسیار دور از دامنه معمول (روش IQR)",
                }
            )

    for column in profile.percent_columns:
        values = pd.to_numeric(clean_df[column], errors="coerce").dropna()
        invalid = int(((values < 0) | (values > 100)).sum())
        if invalid:
            issues.append(
                {
                    "ستون": column,
                    "نوع مشکل": "درصد نامعتبر",
                    "شدت": "بالا",
                    "توضیح": f"{invalid:,} مقدار خارج از بازه ۰ تا ۱۰۰",
                }
            )

    # Constant columns --------------------------------------------------------
    for column in clean_df.columns:
        if clean_df[column].dropna().nunique() == 1 and clean_df[column].notna().any():
            issues.append(
                {
                    "ستون": column,
                    "نوع مشکل": "ستون ثابت",
                    "شدت": "کم",
                    "توضیح": "همه رکوردها یک مقدار دارند و برای تحلیل اطلاعاتی ندارد",
                }
            )

    # Score ---------------------------------------------------------------------
    missing_penalty = min(total_missing / total_cells * 100, 25)
    duplicate_penalty = min(duplicate_rows / rows * 100 * 2, 20)
    high_severity = sum(1 for issue in issues if issue["شدت"] == "بالا")
    medium_severity = sum(1 for issue in issues if issue["شدت"] == "متوسط")
    issue_penalty = min(high_severity * 4 + medium_severity * 2, 35)
    score = max(0.0, 100.0 - missing_penalty - duplicate_penalty - issue_penalty)

    return {
        "score": round(score, 1),
        "issues": issues,
        "total_missing": total_missing,
        "duplicate_rows": duplicate_rows,
        "high_severity": high_severity,
        "medium_severity": medium_severity,
    }
