"""
data_cleaner.py
Converts raw string values from the extractor into numeric form,
standardizes units, and fills missing values.

Unit conversions supported:
  billion → multiply by 1e9
  million → multiply by 1e6
  thousand → multiply by 1e3
  % / percent → divide by 100 to get 0-1 fraction (stored separately)
  MT CO2 → kept as-is (millions of metric tons expected elsewhere)

The output is a tidy pandas DataFrame with one row per (company, metric).
"""

import logging
import re

import pandas as pd

from modules.ai_extractor import ExtractedValue

logger = logging.getLogger(__name__)

# Multipliers for scale words
_SCALE = {
    "billion": 1e9,
    "million": 1e6,
    "thousand": 1e3,
}

_NUM_EXTRACT = re.compile(r"[\d,]+\.?\d*")


def _parse_numeric(raw: str) -> float | None:
    """
    Convert a raw value string to a float, applying scale multipliers.

    Examples:
        "$15.7 billion" → 15_700_000_000.0
        "28%"           → 28.0
        "72 minutes"    → 72.0
        "N/A"           → None
    """
    if not raw or raw.strip().upper() in ("N/A", "NONE", "NULL", ""):
        return None

    raw_lower = raw.lower()

    # Find the first number in the string
    m = _NUM_EXTRACT.search(raw)
    if not m:
        return None

    try:
        num = float(m.group().replace(",", ""))
    except ValueError:
        return None

    # Apply scale
    for word, mult in _SCALE.items():
        if word in raw_lower:
            return num * mult

    return num


def build_raw_df(values: list[ExtractedValue]) -> pd.DataFrame:
    """
    Build the raw data DataFrame directly from extractor output.
    Columns: Company | Metric | Value (raw string) | Source | Source Type
    """
    rows = [
        {
            "Company": v.company,
            "Metric": v.metric,
            "Value": v.raw_value,
            "Source": v.source_url,
            "Source Type": v.source_type,
            "Confidence": v.confidence,
        }
        for v in values
    ]
    return pd.DataFrame(rows)


def build_clean_df(raw_df: pd.DataFrame, expected_metrics: list[str] | None = None) -> pd.DataFrame:
    """
    Produce a cleaned, pivoted DataFrame:
      rows = companies
      columns = metrics
    All values are numeric (float). Missing values are NaN.
    """
    df = raw_df.copy()

    # Parse numeric values
    df["Numeric Value"] = df["Value"].apply(_parse_numeric)

    # Pivot: companies as rows, metrics as columns
    pivot = df.pivot_table(
        index="Company",
        columns="Metric",
        values="Numeric Value",
        aggfunc="first",    # take first occurrence if duplicates
    ).reset_index()

    pivot.columns.name = None   # remove MultiIndex name artifact

    if expected_metrics is not None:
        for metric in expected_metrics:
            if metric not in pivot.columns:
                pivot[metric] = pd.NA
        # Preserve requested metric order after the Company column.
        columns = ["Company"] + [m for m in expected_metrics if m in pivot.columns]
        pivot = pivot[columns]

    return pivot


def fill_missing(clean_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill NaN values with the column mean (industry average imputation).
    Records which cells were imputed so users know.
    Returns the filled DataFrame.
    """
    df = clean_df.copy()
    numeric_cols = [c for c in df.columns if c != "Company"]
    for col in numeric_cols:
        col_mean = df[col].mean()
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            logger.info("Imputing %d missing values in '%s' with mean %.2f", n_missing, col, col_mean)
            df[col] = df[col].fillna(col_mean)
    return df
