"""
config.py
Global constants, default companies/metrics, and metric synonyms.
Extend this file to add new metrics without touching module logic.
"""

import os

# ── Output ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_COMPANIES = [
    "Con Edison",
    "National Grid",
    "Pacific Gas and Electric",
    "Duke Energy",
    "Consolidated Edison",
]

DEFAULT_METRICS = [
    "Revenue",
    "Renewable Energy %",
    "Outage Frequency",
    "Customer Satisfaction Score",
    "Carbon Emissions (MT CO2)",
]

# ── Metric synonyms (AI extractor uses this to normalize terminology) ─────────
METRIC_SYNONYMS: dict[str, list[str]] = {
    "Revenue": ["total revenue", "net revenue", "sales", "total sales", "operating revenue"],
    "Renewable Energy %": [
        "renewable energy percentage", "clean energy %", "renewables share",
        "green energy fraction", "% renewable", "renewable mix",
    ],
    "Outage Frequency": [
        "saidi", "saifi", "outage minutes", "power interruptions",
        "reliability index", "unplanned outages",
    ],
    "Customer Satisfaction Score": [
        "csat", "j.d. power score", "customer rating", "satisfaction index",
        "nps", "net promoter score",
    ],
    "Carbon Emissions (MT CO2)": [
        "co2 emissions", "greenhouse gas", "ghg emissions", "carbon footprint",
        "scope 1 emissions", "total emissions",
    ],
}

# ── Known company ticker symbols for optional API enrichment ────────────────
COMPANY_TICKERS = {
    "con edison": "ED",
    "consolidated edison": "ED",
    "national grid": "NGG",
    "pacific gas and electric": "PCG",
    "duke energy": "DUK",
    "eversource energy": "ES",
    "southern company": "SO",
}

# ── Scraping ──────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 10   # seconds
USER_AGENT = (
    "Mozilla/5.0 (compatible; BenchmarkBot/1.0; "
    "+https://example.com/benchmarkbot)"
)

# ── LLM ───────────────────────────────────────────────────────────────────────
# Set OPENAI_API_KEY in environment to enable real LLM extraction.
# If unset, the extractor falls back to the rule-based simulator.
OPENAI_MODEL = "gpt-4o-mini"
USE_REAL_LLM = bool(os.getenv("OPENAI_API_KEY"))
