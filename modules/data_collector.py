"""
data_collector.py
Fetches raw text for each company from public sources.

Strategy (in order of preference):
1. Financial API  — tries a free endpoint (e.g. Alpha Vantage) for revenue
2. Web scrape     — fetches the company's investor-relations / ESG page
3. Simulated data — deterministic fallback so the prototype always runs

Each collected snippet is stored as a CollectedDoc so every downstream
module can trace which URL a value came from.
"""

import hashlib
import json
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from modules.config import REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class CollectedDoc:
    company: str
    source_url: str
    source_type: str          # "api" | "scrape" | "simulated"
    raw_text: str


# ── Simulated fallback data ────────────────────────────────────────────────────
# Keyed by lowercase company name. Values are realistic but illustrative.
# Extend this dict or replace with a JSON file for larger prototypes.

SIMULATED_DATA: dict[str, str] = {
    "con edison": """
        Con Edison reported total revenue of $15.7 billion for fiscal year 2023.
        The company achieved a renewable energy percentage of 28% of its energy mix.
        SAIDI (outage frequency) was 72 minutes per customer.
        Customer satisfaction score was 74 out of 100 per J.D. Power.
        Carbon emissions were 4.2 million metric tons of CO2 equivalent.
    """,
    "national grid": """
        National Grid plc reported operating revenue of $22.1 billion.
        Renewable energy share reached 35% of total generation capacity.
        Average outage frequency index was 58 minutes (SAIDI).
        Net promoter score was 61.
        Scope 1 GHG emissions totaled 3.8 million MT CO2.
    """,
    "pacific gas and electric": """
        PG&E total revenue was $24.4 billion in 2023.
        Clean energy percentage stands at 39% including hydro and solar.
        Power interruptions (SAIFI) averaged 1.2 per customer annually.
        J.D. Power residential satisfaction index: 668 (out of 1000).
        Greenhouse gas emissions: 5.1 million metric tons CO2.
    """,
    "duke energy": """
        Duke Energy net revenue: $28.8 billion fiscal 2023.
        Renewables mix is 21% of total portfolio.
        Outage minutes per customer: 90 (SAIDI).
        Customer satisfaction score of 71/100.
        Total carbon footprint: 68 million MT CO2.
    """,
    "consolidated edison": """
        Consolidated Edison revenues of $15.7 billion.
        28% of supply sourced from renewable energy.
        System Average Interruption Duration Index: 72 minutes.
        CSAT score: 74.
        CO2 equivalent emissions: 4.2 million metric tons.
    """,
    "eversource energy": """
        Eversource reported $12.3 billion total revenue in 2023.
        Renewable energy percentage: 31%.
        SAIDI outage frequency: 65 minutes.
        Customer satisfaction (J.D. Power): 79 out of 100.
        Carbon emissions: 2.9 million MT CO2.
    """,
    "southern company": """
        Southern Company total revenues: $23.6 billion.
        Renewable energy share: 17%.
        Outage duration: 95 minutes SAIDI.
        Customer satisfaction score: 69.
        Greenhouse gas emissions: 72 million MT CO2.
    """,
}


# ── Scraping helpers ──────────────────────────────────────────────────────────

def _build_search_url(company: str) -> str:
    """Construct a DuckDuckGo lite search URL for the company's annual report."""
    q = f"{company} annual report 2023 investor relations"
    return f"https://html.duckduckgo.com/html/?q={requests.utils.quote(q)}"


def _scrape_page(url: str) -> str:
    """Fetch a URL and return its visible text (best-effort)."""
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    # Remove script/style noise
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)[:8000]   # cap at 8 k chars


def _get_simulated(company: str) -> str | None:
    """Return simulated text for a company if available."""
    return SIMULATED_DATA.get(company.lower())


# ── Public interface ──────────────────────────────────────────────────────────

def collect_for_company(company: str) -> CollectedDoc:
    """
    Collect raw text for a single company.

    Tries live scraping first; falls back to simulated data.
    Logs each attempt so failures are transparent.
    """
    # 1. Try live scrape (search result page → first result URL ideally)
    try:
        search_url = _build_search_url(company)
        text = _scrape_page(search_url)
        if len(text) > 200:     # sanity check — not a redirect / empty page
            logger.info("Scraped search results for %s", company)
            return CollectedDoc(
                company=company,
                source_url=search_url,
                source_type="scrape",
                raw_text=text,
            )
    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", company, exc)

    # 2. Fall back to simulated data
    sim = _get_simulated(company)
    if sim:
        logger.info("Using simulated data for %s", company)
        return CollectedDoc(
            company=company,
            source_url="simulated://internal",
            source_type="simulated",
            raw_text=sim,
        )

    # 3. Return an empty doc so the pipeline continues (with missing values)
    logger.warning("No data found for %s; returning empty doc", company)
    return CollectedDoc(
        company=company,
        source_url="none",
        source_type="none",
        raw_text="",
    )


def collect_all(companies: list[str]) -> list[CollectedDoc]:
    """Collect docs for all companies with a polite crawl delay."""
    docs = []
    for i, company in enumerate(companies):
        doc = collect_for_company(company)
        docs.append(doc)
        if i < len(companies) - 1:
            time.sleep(0.5)   # be polite to servers
    return docs
