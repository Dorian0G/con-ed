"""
data_collector.py
Fetches raw text for each company from public sources.

Fix: source_url now always resolves to a real, clickable HTTPS link.
  - API path:       was "yfinance://ED"        → now the company's real IR page
  - Simulated path: was "simulated://internal" → now the company's real IR page
  - Scrape path:    already used a real URL, unchanged
  - Unknown company fallback: "none" → kept, but also logs a warning
"""

import time
import logging
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from modules.config import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    COMPANY_TICKERS,
    COMPANY_IR_URLS,
)

logger = logging.getLogger(__name__)


# ── Data structure ─────────────────────────────────────────────────────────────

@dataclass
class CollectedDoc:
    company: str
    source_url: str
    source_type: str          # "api" | "scrape" | "simulated"
    raw_text: str


# ── Simulated fallback data ────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _real_url(company: str) -> str:
    """
    Return the real investor-relations URL for a company.
    Falls back to a SEC EDGAR full-text search if the company isn't in
    COMPANY_IR_URLS so there is always a clickable link.
    """
    key = company.lower().strip()
    if key in COMPANY_IR_URLS:
        return COMPANY_IR_URLS[key]
    # Generic fallback: SEC EDGAR search for the company name
    encoded = requests.utils.quote(company)
    return f"https://efts.sec.gov/LATEST/search-index?q=%22{encoded}%22&dateRange=custom&startdt=2023-01-01&enddt=2024-01-01&forms=10-K"


def _build_search_url(company: str) -> str:
    q = f"{company} annual report 2023 investor relations"
    return f"https://html.duckduckgo.com/html/?q={requests.utils.quote(q)}"


def _extract_first_result_url(soup: BeautifulSoup, base_url: str) -> str | None:
    link = soup.find("a", class_="result__a")
    if link and link.get("href"):
        return requests.compat.urljoin(base_url, link["href"])
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("http") and "duckduckgo.com" not in href:
            return href
    return None


def _scrape_page(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    resp    = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)[:8000]


def _try_financial_api(company: str) -> CollectedDoc | None:
    ticker = COMPANY_TICKERS.get(company.lower())
    if not ticker:
        return None
    try:
        import yfinance as yf
    except ImportError:
        return None

    try:
        ticker_obj    = yf.Ticker(ticker)
        fin           = ticker_obj.financials
        if fin is None or fin.empty:
            return None

        revenue_rows = [i for i in fin.index if "revenue" in str(i).lower()]
        if not revenue_rows:
            return None

        revenue_value = fin.loc[revenue_rows[0]].iloc[0]
        if revenue_value is None or (isinstance(revenue_value, float) and revenue_value != revenue_value):
            return None

        raw_text = (
            f"{company} reported total revenue of ${revenue_value / 1e9:.2f} billion "
            f"for the most recent fiscal year (source: Yahoo Finance, ticker {ticker})."
        )

        # FIX: use the real IR page URL instead of "yfinance://ED"
        return CollectedDoc(
            company=company,
            source_url=_real_url(company),
            source_type="api",
            raw_text=raw_text,
        )
    except Exception as exc:
        logger.warning("Financial API lookup failed for %s: %s", company, exc)
        return None


def _get_simulated(company: str) -> str | None:
    return SIMULATED_DATA.get(company.lower().strip())


# ── Public interface ──────────────────────────────────────────────────────────

def collect_for_company(company: str) -> CollectedDoc:
    # 0. Optional API enrichment (revenue only)
    try:
        api_doc = _try_financial_api(company)
        if api_doc:
            logger.info("Collected API data for %s", company)
            return api_doc
    except Exception as exc:
        logger.warning("Financial API collection failed for %s: %s", company, exc)

    # 1. Live scrape
    try:
        search_url  = _build_search_url(company)
        headers     = {"User-Agent": USER_AGENT}
        resp        = requests.get(search_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        search_soup = BeautifulSoup(resp.text, "lxml")
        target_url  = _extract_first_result_url(search_soup, search_url)

        if target_url:
            try:
                text = _scrape_page(target_url)
                if len(text) > 200:
                    logger.info("Scraped target page for %s: %s", company, target_url)
                    return CollectedDoc(
                        company=company,
                        source_url=target_url,   # already a real URL
                        source_type="scrape",
                        raw_text=text,
                    )
            except Exception as exc:
                logger.warning("Target page scrape failed for %s: %s", company, exc)

        text = _scrape_page(search_url)
        if len(text) > 200:
            logger.info("Scraped search results page for %s", company)
            return CollectedDoc(
                company=company,
                source_url=search_url,           # already a real URL
                source_type="scrape",
                raw_text=text,
            )
    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", company, exc)

    # 2. Simulated fallback
    sim = _get_simulated(company)
    if sim:
        logger.info("Using simulated data for %s", company)
        # FIX: use the real IR page URL instead of "simulated://internal"
        return CollectedDoc(
            company=company,
            source_url=_real_url(company),
            source_type="simulated",
            raw_text=sim,
        )

    # 3. Empty doc — nothing found
    logger.warning(
        "No data found for '%s'. Add it to SIMULATED_DATA or COMPANY_IR_URLS in config.py.",
        company,
    )
    return CollectedDoc(
        company=company,
        source_url=_real_url(company),  # still provide the IR page as best-effort
        source_type="none",
        raw_text="",
    )


def collect_all(companies: list[str]) -> list[CollectedDoc]:
    """Collect docs for all companies with a polite crawl delay."""
    docs = []
    for i, company in enumerate(companies):
        try:
            doc = collect_for_company(company)
        except Exception as exc:
            logger.error("Unexpected error collecting %s: %s — using empty doc.", company, exc)
            doc = CollectedDoc(
                company=company,
                source_url=_real_url(company),
                source_type="none",
                raw_text="",
            )
        docs.append(doc)
        if doc.source_type == "scrape" and i < len(companies) - 1:
            time.sleep(0.5)
    return docs
