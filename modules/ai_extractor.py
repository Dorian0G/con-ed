"""
ai_extractor.py
Extracts metric values from raw text using either a real LLM (OpenAI)
or a robust rule-based simulator.

Design decisions:
- The same ExtractedValue dataclass is returned regardless of backend,
  so swapping real vs. simulated has zero effect on downstream modules.
- The rule-based extractor uses regex + synonym matching from config.py
  rather than hardcoded patterns — adding a new metric only requires
  updating METRIC_SYNONYMS in config.py.
- When USE_REAL_LLM is True and an API key is set, the LLM prompt is
  structured so the model returns valid JSON, which is then parsed safely.
"""

import json
import logging
import re
from dataclasses import dataclass

from modules.config import METRIC_SYNONYMS, OPENAI_MODEL, USE_REAL_LLM
from modules.data_collector import CollectedDoc

logger = logging.getLogger(__name__)


# ── Data structure ─────────────────────────────────────────────────────────────

@dataclass
class ExtractedValue:
    company: str
    metric: str
    raw_value: str           # exactly as found in text
    source_url: str
    source_type: str
    confidence: float        # 0.0 – 1.0


# ── Rule-based (simulated) extractor ──────────────────────────────────────────

# Number pattern: matches values like "$15.7 billion", "28%", "72 minutes"
_NUM_RE = re.compile(
    r"""
    (?:\$\s*)?              # optional dollar sign
    (\d{1,3}(?:[,\.]\d+)*)  # integer or decimal, with commas ok
    \s*
    (billion|million|thousand|%|percent|minutes?|mt|score|points?)?
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _find_value_near_keyword(text: str, keywords: list[str]) -> str | None:
    """
    Search for a numeric value in sentences containing any keyword.
    Returns the first match as a raw string, or None.
    """
    sentences = re.split(r"[.\n]+", text)
    for kw in keywords:
        for sentence in sentences:
            if kw.lower() in sentence.lower():
                m = _NUM_RE.search(sentence)
                if m:
                    # Reconstruct the matched value with its unit
                    num = m.group(1)
                    unit = m.group(2) or ""
                    return f"{num} {unit}".strip()
    return None


def extract_rule_based(doc: CollectedDoc, metrics: list[str]) -> list[ExtractedValue]:
    """Rule-based extraction using synonym matching and regex."""
    results = []
    for metric in metrics:
        synonyms = METRIC_SYNONYMS.get(metric, [metric])
        all_keywords = [metric] + synonyms
        raw = _find_value_near_keyword(doc.raw_text, all_keywords)
        results.append(
            ExtractedValue(
                company=doc.company,
                metric=metric,
                raw_value=raw or "N/A",
                source_url=doc.source_url,
                source_type=doc.source_type,
                confidence=0.75 if raw else 0.0,
            )
        )
    return results


# ── LLM-based extractor ────────────────────────────────────────────────────────

def _build_llm_prompt(company: str, metrics: list[str], text: str) -> str:
    metric_list = "\n".join(f"- {m}" for m in metrics)
    return f"""
You are a financial data analyst. Extract the following metrics for {company}
from the text below. Return ONLY valid JSON — no markdown, no explanation.

Metrics to extract:
{metric_list}

Text:
{text[:4000]}

Return format:
{{
  "metrics": {{
    "<metric name>": "<value as string, including unit, or null if not found>"
  }}
}}
"""


def extract_llm(doc: CollectedDoc, metrics: list[str]) -> list[ExtractedValue]:
    """LLM-based extraction via OpenAI API."""
    try:
        from openai import OpenAI
        client = OpenAI()
        prompt = _build_llm_prompt(doc.company, metrics, doc.raw_text)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_json = response.choices[0].message.content or "{}"
        # Strip accidental markdown fences
        raw_json = re.sub(r"```json|```", "", raw_json).strip()
        data = json.loads(raw_json)
        extracted = data.get("metrics", {})
    except Exception as exc:
        logger.warning("LLM extraction failed for %s: %s. Falling back.", doc.company, exc)
        return extract_rule_based(doc, metrics)

    results = []
    for metric in metrics:
        val = extracted.get(metric)
        results.append(
            ExtractedValue(
                company=doc.company,
                metric=metric,
                raw_value=val if val else "N/A",
                source_url=doc.source_url,
                source_type=f"{doc.source_type}+llm",
                confidence=0.9 if val else 0.0,
            )
        )
    return results


# ── Public interface ──────────────────────────────────────────────────────────

def extract_metrics(docs: list[CollectedDoc], metrics: list[str]) -> list[ExtractedValue]:
    """
    Extract all metrics from all collected docs.
    Uses LLM if configured, otherwise rule-based.
    """
    all_values: list[ExtractedValue] = []
    extractor = extract_llm if USE_REAL_LLM else extract_rule_based
    for doc in docs:
        values = extractor(doc, metrics)
        all_values.extend(values)
    return all_values
