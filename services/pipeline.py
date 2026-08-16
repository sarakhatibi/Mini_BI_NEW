"""End-to-end analysis pipeline: load → clean → profile → analyse."""

from dataclasses import dataclass

import pandas as pd

from services.data_analyzer import analyze_dataset, assess_quality
from services.data_cleaner import CleaningResult, clean_dataset
from services.semantic_profiler import DatasetProfile, profile_dataset


@dataclass
class AnalysisBundle:
    raw_data: pd.DataFrame
    data: pd.DataFrame
    cleaning: CleaningResult
    profile: DatasetProfile
    structure: dict
    quality: dict


def build_analysis(raw_df: pd.DataFrame) -> AnalysisBundle:
    """Run the full preparation pipeline on a freshly loaded DataFrame."""
    cleaning = clean_dataset(raw_df)
    profile = profile_dataset(cleaning.data)
    structure = analyze_dataset(cleaning.data, profile)
    quality = assess_quality(raw_df, cleaning.data, cleaning, profile)

    return AnalysisBundle(
        raw_data=raw_df,
        data=cleaning.data,
        cleaning=cleaning,
        profile=profile,
        structure=structure,
        quality=quality,
    )
