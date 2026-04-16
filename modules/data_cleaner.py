"""
data_cleaner.py
Converts raw extracted strings to numeric values in natural display units.
 
Display units:
  Revenue                     ->  $B          15.26  = $15.26 billion
  Renewable Energy %          ->  %           30.0   = 30%
  Outage Frequency            ->  minutes     55.0   = 55 min SAIDI
  Customer Satisfaction Score ->  /100        73.0   = 730/1000 normalised
  Carbon Emissions (MT CO2)   ->  M MT CO2    2.35   = 2.35 million metric tons
 
Note on Customer Satisfaction:
  J.D. Power scores are reported on a /1000 scale.
  The divisor for this metric is 10, converting 730 -> 73.0 (/100).
"""
 
import logging
import re
 
import pandas as pd
 
from modules.ai_extractor import ExtractedValue
 
logger = logging.getLogger(__name__)
 
_DIVISOR: dict[str, float] = {
    "revenue":                      1_000_000_000,  # raw dollars -> $B
    "renewable energy %":           1.0,
    "outage frequency":             1.0,             # already minutes
    "customer satisfaction score":  10.0,            # /1000 JD Power -> /100
    "carbon emissions (mt co2)":    1_000_000,       # raw tonnes -> M MT
}
 
_SCALE: dict[str, float] = {
    "billion":  1_000_000_000,
    "million":  1_000_000,
    "thousand": 1_000,
}
 
_NUM_RE = re.compile(r"\d[\d,]*\.?\d*")
 
 
def _parse_numeric(raw: str, metric: str = "") -> float | None:
    """
    Convert a raw string to a float in display units.
    Applies scale words (billion/million) then per-metric divisor.
    """
    if not raw or raw.strip().upper() in ("N/A", "NONE", "NULL", ""):
        return None
 
    raw_lower = raw.lower()
 
    m = _NUM_RE.search(raw)
    if not m:
        return None
 
    try:
        num = float(m.group().replace(",", ""))
    except ValueError:
        return None
 
    for word, mult in _SCALE.items():
        if word in raw_lower:
            num *= mult
            break
 
    divisor = _DIVISOR.get(metric.lower().strip(), 1.0)
    return round(num / divisor, 4)
 
 
def build_raw_df(values: list[ExtractedValue]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Company":     v.company,
            "Metric":      v.metric,
            "Value":       v.raw_value,
            "Source":      v.source_url,
            "Source Type": v.source_type,
            "Confidence":  v.confidence,
        }
        for v in values
    ])
 
 
def build_clean_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["Numeric Value"] = df.apply(
        lambda row: _parse_numeric(row["Value"], row["Metric"]),
        axis=1,
    )
    all_companies = df["Company"].unique().tolist()
    all_metrics   = df["Metric"].unique().tolist()
 
    pivot = (
        df.pivot_table(
            index="Company",
            columns="Metric",
            values="Numeric Value",
            aggfunc="first",
        )
        .reset_index()
    )
    pivot.columns.name = None
    pivot = (
        pivot
        .set_index("Company")
        .reindex(index=all_companies, columns=all_metrics)
        .reset_index()
    )
    pivot.columns.name = None
    return pivot
 
 
def fill_missing(clean_df: pd.DataFrame) -> pd.DataFrame:
    df = clean_df.copy()
    for col in [c for c in df.columns if c != "Company"]:
        col_mean = df[col].mean()
        n = df[col].isna().sum()
        if n:
            logger.info("Imputing %d missing in '%s' with mean %.4f", n, col, col_mean)
            df[col] = df[col].fillna(col_mean)
    return df
 
