"""
copilot_bridge.py
Generates a structured, ready-to-paste prompt for Microsoft Copilot
(copilot.microsoft.com — free, public, no API key required).

Design rationale:
- Instead of calling any AI API, we embed the benchmark data directly
  inside a well-structured natural-language prompt.
- The user pastes this into the public Copilot chat and gets executive
  summaries, slide drafts, or strategic recommendations instantly.
- The prompt is also saved as a sheet in the Excel output so it travels
  with the workbook.
"""

import pandas as pd
from modules.benchmark_engine import LOWER_IS_BETTER


def _format_table(bench_df: pd.DataFrame) -> str:
    """Build a compact plain-text table of benchmark results."""
    if bench_df.empty or "Metric" not in bench_df.columns:
        return "No benchmark data available."

    metrics = bench_df["Metric"].unique().tolist()
    lines = []

    for metric in metrics:
        direction = "lower is better" if metric in LOWER_IS_BETTER else "higher is better"
        lines.append(f"\n{metric}  ({direction})")
        lines.append(f"  {'Company':<32} {'Value':>14}  {'Rank':>5}  {'Percentile':>10}")
        lines.append("  " + "-" * 65)
        sub = bench_df[bench_df["Metric"] == metric].sort_values("Rank")
        for _, row in sub.iterrows():
            val = f"{row['Value']:,.2f}" if pd.notna(row["Value"]) else "N/A"
            lines.append(
                f"  {row['Company']:<32} {val:>14}  {int(row['Rank']):>5}  {row['Percentile']:>9.1f}%"
            )
        avg = sub["Industry Average"].iloc[0]
        lines.append(f"  {'Industry average':<32} {avg:>14,.2f}")

    return "\n".join(lines)


def build_copilot_prompt(
    bench_df: pd.DataFrame,
    companies: list[str],
    metrics: list[str],
) -> str:
    """
    Return a fully self-contained prompt string ready to paste into
    copilot.microsoft.com.

    The prompt:
    1. Sets the context (who, what, why)
    2. Embeds the full benchmark data as plain text
    3. Asks for specific, useful outputs
    4. Includes follow-up suggestions
    """
    table = _format_table(bench_df)
    company_list = ", ".join(companies)
    metric_list  = ", ".join(metrics)

    prompt = f"""
You are an expert utility industry analyst. I have run a competitive benchmark
analysis on the following energy companies: {company_list}.

The metrics analysed are: {metric_list}.

Below is the full benchmark data. Please:
1. Write an executive summary (4–6 sentences) identifying the top performers,
   underperformers, and the most significant gaps.
2. List 3 strategic recommendations for a mid-tier performer in this peer group.
3. Suggest 2 additional metrics this analysis should include in future.

────────────────────────────────────────────────────────────────
BENCHMARK DATA
────────────────────────────────────────────────────────────────
{table}
────────────────────────────────────────────────────────────────

Notes:
- Rank 1 = best performer for each metric.
- Percentile scores are relative within this peer group (100 = best).
- Values marked "lower is better" (e.g. outage frequency, emissions) are
  ranked so that the lowest value receives rank 1.
- Industry average is the unweighted mean across all companies shown.

Please begin with the executive summary.
""".strip()

    return prompt
