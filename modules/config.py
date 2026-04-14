"""
config.py
Global constants, default companies/metrics, and metric synonyms.
Extend this file to add new metrics without touching module logic.
"""

import os
import requests
from datetime import datetime

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Dynamic report year ───────────────────────────────────────────────────────
def current_report_year() -> int:
    now = datetime.now()
    return now.year - 1 if now.month >= 4 else now.year - 2

REPORT_YEAR: int = current_report_year()

# ── Defaults ──────────────────────────────────────────────────────────────────
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

# ── Metric synonyms ───────────────────────────────────────────────────────────
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

# ── Known company ticker symbols for optional API enrichment ─────────────────
COMPANY_TICKERS: dict[str, str] = {
    "con edison":               "ED",
    "consolidated edison":      "ED",
    "national grid":            "NGG",
    "pacific gas and electric": "PCG",
    "duke energy":              "DUK",
    "eversource energy":        "ES",
    "southern company":         "SO",
}

# ── Fallback IR landing pages ─────────────────────────────────────────────────
COMPANY_IR_URLS: dict[str, str] = {
    "con edison":               "https://investor.conedison.com/financial-information/annual-reports",
    "consolidated edison":      "https://investor.conedison.com/financial-information/annual-reports",
    "national grid":            "https://www.nationalgrid.com/investors/resources/reports-plc",
    "pacific gas and electric": "https://investor.pgecorp.com/financial-information/annual-reports-and-proxy",
    "duke energy":              "https://investors.duke-energy.com/financial-information/annual-reports",
    "eversource energy":        "https://investor.eversource.com/financial-information/annual-reports",
    "southern company":         "https://investor.southerncompany.com/financial-information/annual-reports",
}

# ── Per-metric source URLs (built dynamically from REPORT_YEAR) ───────────────
def _build_metric_urls(year: int) -> dict[tuple[str, str], str]:
    y = str(year)
    return {
        # ── Con Edison / Consolidated Edison ──────────────────────────────────
        ("con edison", "revenue"):
            "https://investor.conedison.com/sec-filings/annual-filings",
        ("con edison", "renewable energy %"):
            f"https://lite.conedison.com/ehs/{y}-sustainability-report/report-introduction/our-sustainability-strategy/",
        ("con edison", "outage frequency"):
            "https://investor.conedison.com/sec-filings/annual-filings",
        ("con edison", "customer satisfaction score"):
            "https://investor.conedison.com/sec-filings/annual-filings",
        ("con edison", "carbon emissions (mt co2)"):
            f"https://lite.conedison.com/ehs/{y}-sustainability-report/environment/managing-our-emissions/",

        ("consolidated edison", "revenue"):
            "https://investor.conedison.com/sec-filings/annual-filings",
        ("consolidated edison", "renewable energy %"):
            f"https://lite.conedison.com/ehs/{y}-sustainability-report/report-introduction/our-sustainability-strategy/",
        ("consolidated edison", "outage frequency"):
            "https://investor.conedison.com/sec-filings/annual-filings",
        ("consolidated edison", "customer satisfaction score"):
            "https://investor.conedison.com/sec-filings/annual-filings",
        ("consolidated edison", "carbon emissions (mt co2)"):
            f"https://lite.conedison.com/ehs/{y}-sustainability-report/environment/managing-our-emissions/",

        # ── National Grid ─────────────────────────────────────────────────────
        ("national grid", "revenue"):
            "https://www.nationalgrid.com/investors/resources/reports-plc",
        ("national grid", "renewable energy %"):
            "https://www.nationalgridus.com/responsible-business-commitments",
        ("national grid", "outage frequency"):
            "https://www.nationalgrid.com/investors/resources/reports-plc",
        ("national grid", "customer satisfaction score"):
            "https://www.nationalgrid.com/investors/resources/reports-plc",
        ("national grid", "carbon emissions (mt co2)"):
            "https://www.nationalgrid.com/investors/resources/reports-plc",

        # ── Pacific Gas and Electric ───────────────────────────────────────────
        ("pacific gas and electric", "revenue"):
            "https://investor.pgecorp.com/financial-information/annual-reports-and-proxy",
        ("pacific gas and electric", "renewable energy %"):
            f"https://www.pgecorp.com/corp_responsibility/reports/{y}/en/index.html",
        ("pacific gas and electric", "outage frequency"):
            "https://investor.pgecorp.com/financial-information/annual-reports-and-proxy",
        ("pacific gas and electric", "customer satisfaction score"):
            "https://investor.pgecorp.com/financial-information/annual-reports-and-proxy",
        ("pacific gas and electric", "carbon emissions (mt co2)"):
            f"https://www.pgecorp.com/corp_responsibility/reports/{y}/en/index.html",

        # ── Duke Energy ───────────────────────────────────────────────────────
        ("duke energy", "revenue"):
            "https://investors.duke-energy.com/financial-information/annual-reports",
        ("duke energy", "renewable energy %"):
            "https://p-micro.duke-energy.com/impact/esg-resources",
        ("duke energy", "outage frequency"):
            "https://investors.duke-energy.com/financial-information/annual-reports",
        ("duke energy", "customer satisfaction score"):
            "https://investors.duke-energy.com/financial-information/annual-reports",
        ("duke energy", "carbon emissions (mt co2)"):
            f"https://p-micro.duke-energy.com/annual-report/-/media/pdfs/our-company/investors/de-annual-reports/{y}/{y}-duke-energy-annual-report.pdf",

        # ── Eversource Energy ─────────────────────────────────────────────────
        ("eversource energy", "revenue"):
            "https://investor.eversource.com/financial-information/annual-reports",
        ("eversource energy", "renewable energy %"):
            "https://www.eversource.com/content/residential/about/sustainability/reporting-and-disclosures",
        ("eversource energy", "outage frequency"):
            "https://investor.eversource.com/financial-information/annual-reports",
        ("eversource energy", "customer satisfaction score"):
            "https://investor.eversource.com/financial-information/annual-reports",
        ("eversource energy", "carbon emissions (mt co2)"):
            "https://www.eversource.com/content/residential/about/sustainability/reporting-and-disclosures",

        # ── Southern Company ──────────────────────────────────────────────────
        ("southern company", "revenue"):
            "https://investor.southerncompany.com/financial-information/annual-reports",
        ("southern company", "renewable energy %"):
            "https://investor.southerncompany.com/sustainability",
        ("southern company", "outage frequency"):
            "https://investor.southerncompany.com/financial-information/annual-reports",
        ("southern company", "customer satisfaction score"):
            "https://investor.southerncompany.com/financial-information/annual-reports",
        ("southern company", "carbon emissions (mt co2)"):
            "https://investor.southerncompany.com/sustainability",
    }

METRIC_SOURCE_URLS: dict[tuple[str, str], str] = _build_metric_urls(REPORT_YEAR)

# ── Scraping ──────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 10
USER_AGENT = (
    "Mozilla/5.0 (compatible; BenchmarkBot/1.0; "
    "+https://example.com/benchmarkbot)"
)

# ── LLM ───────────────────────────────────────────────────────────────────────
OPENAI_MODEL = "gpt-4o-mini"
USE_REAL_LLM = bool(os.getenv("OPENAI_API_KEY"))
