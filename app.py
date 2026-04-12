"""
app.py  —  Utility Benchmark Tool
Streamlit web app. No API keys required. All data is publicly accessible.
Copilot integration is achieved by generating a pre-written prompt the user
pastes into copilot.microsoft.com — no API key, no backend auth.

Run locally:
    streamlit run app.py

Deploy free:
    streamlit.io/cloud  (connect GitHub repo, set entry point = app.py)
"""

import logging
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from modules.config import DEFAULT_COMPANIES, DEFAULT_METRICS
from modules.input_handler import parse_input
from modules.data_collector import collect_all
from modules.ai_extractor import extract_metrics
from modules.data_cleaner import build_raw_df, build_clean_df, fill_missing
from modules.benchmark_engine import build_benchmark
from modules.insight_generator import generate_insights
from modules.output_generator import generate_excel
from modules.copilot_bridge import build_copilot_prompt

logging.basicConfig(level=logging.INFO)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Utility Benchmark Tool",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; }
    .copilot-box {
        background: #f0f4ff;
        border: 1px solid #c5d3f5;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-family: monospace;
        font-size: 0.82rem;
        white-space: pre-wrap;
        color: #1a1a2e;
        max-height: 340px;
        overflow-y: auto;
    }
    .copilot-tip {
        background: #eaf6ff;
        border-left: 4px solid #0078d4;
        border-radius: 4px;
        padding: 0.6rem 1rem;
        font-size: 0.88rem;
        color: #003a70;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: inputs ────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Lightning_bolt_simple.svg/240px-Lightning_bolt_simple.svg.png",
        width=48,
    )
    st.title("Utility Benchmark Tool")
    st.caption("Competitive intelligence for energy companies — no account required.")
    st.divider()

    st.subheader("🏢 Companies")
    companies_raw = st.text_area(
        "One company per line",
        value="\n".join(DEFAULT_COMPANIES[:4]),
        height=130,
        help="Enter publicly listed or well-known utility companies.",
    )

    st.subheader("📐 Metrics")
    metrics_raw = st.text_area(
        "One metric per line",
        value="\n".join(DEFAULT_METRICS),
        height=130,
        help="Standard financial, ESG, or reliability metrics.",
    )

    run_btn = st.button("🚀 Run Benchmark", use_container_width=True, type="primary")

    st.divider()
    st.markdown("""
**Data sources used:**
- Public web / investor-relations pages
- Simulated fallback (clearly labelled)

**No API keys required.**
[Deploy your own copy →](https://share.streamlit.io)
""")

# ── Main panel ─────────────────────────────────────────────────────────────────
st.title("⚡ Utility Company Benchmark Analysis")
st.caption("Publicly available data · No sign-in required · Microsoft Copilot ready")

if not run_btn:
    col1, col2, col3 = st.columns(3)
    col1.metric("Companies supported", "2 – 10")
    col2.metric("Metrics supported", "3 – 10")
    col3.metric("Export formats", "Excel + Copilot prompt")
    st.info("Enter companies and metrics in the sidebar, then click **Run Benchmark**.")
    st.stop()

# ── Parse input ────────────────────────────────────────────────────────────────
companies = [c for c in companies_raw.strip().splitlines() if c.strip()]
metrics   = [m for m in metrics_raw.strip().splitlines()   if m.strip()]

try:
    request = parse_input(companies, metrics)
except ValueError as e:
    st.error(str(e))
    st.stop()

# ── Run pipeline ───────────────────────────────────────────────────────────────
progress = st.progress(0, text="Starting…")

progress.progress(10, text="🔍 Collecting public data…")
docs = collect_all(request.companies)

progress.progress(35, text="🧠 Extracting metrics from text…")
extracted = extract_metrics(docs, request.metrics)

progress.progress(55, text="🧹 Cleaning and normalizing…")
raw_df    = build_raw_df(extracted)
clean_df  = build_clean_df(raw_df)
filled_df = fill_missing(clean_df)

progress.progress(72, text="📊 Computing rankings…")
bench_df  = build_benchmark(filled_df)

progress.progress(87, text="💡 Generating insights…")
insights  = generate_insights(bench_df)

copilot_prompt = build_copilot_prompt(bench_df, request.companies, request.metrics)

progress.progress(95, text="📦 Preparing Excel…")
excel_bytes = generate_excel(
    raw_df,
    clean_df,
    bench_df,
    insights,
    copilot_prompt=copilot_prompt,
)

progress.progress(100, text="✅ Done!")

# ── Results ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Benchmark", "🧹 Clean Data", "📄 Raw Data", "💡 Insights", "🤖 Copilot"
])

with tab1:
    st.subheader("Benchmark Summary")
    if bench_df.empty or "Metric" not in bench_df.columns:
        st.warning("No benchmark data available. Please check your inputs.")
    else:
        display = bench_df[["Company", "Metric", "Value", "Rank", "Industry Average", "Percentile"]]
        # FIX: was outside this block due to indentation error; also replaced
        # background_gradient (requires matplotlib) with bar (no extra deps)
        st.dataframe(
            display.style.bar(
                subset=["Percentile"],
                color="#4A90D9",
                vmin=0,
                vmax=100,
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.divider()
        sel = st.selectbox("Chart a metric", bench_df["Metric"].unique().tolist())
        chart_data = (
            bench_df[bench_df["Metric"] == sel]
            .set_index("Company")["Value"]
            .sort_values(ascending=False)
        )
        st.bar_chart(chart_data)

with tab2:
    st.subheader("Cleaned & Normalized Data")
    st.dataframe(filled_df, use_container_width=True, hide_index=True)
    st.caption("Missing values imputed with column mean (industry average).")

with tab3:
    st.subheader("Raw Extracted Data")
    st.dataframe(raw_df, use_container_width=True, hide_index=True)
    sim_count = (raw_df["Source Type"] == "simulated").sum()
    if sim_count:
        st.warning(
            f"⚠️  {sim_count} values are from simulated fallback data "
            "(live scraping returned no result). Verify against primary sources."
        )

with tab4:
    st.subheader("AI-Generated Insights")
    st.markdown(insights)

with tab5:
    st.subheader("🤖 Microsoft Copilot Integration")
    st.markdown("""
<div class="copilot-tip">
<strong>No API required.</strong> Copy the prompt below and paste it into
<a href="https://copilot.microsoft.com" target="_blank">copilot.microsoft.com</a>
(free, sign-in with any Microsoft account). Copilot will generate an executive
summary, slide talking points, or a deeper analysis — your choice.
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Ready-to-paste Copilot prompt")
    st.markdown(f'<div class="copilot-box">{copilot_prompt}</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    col_a.button(
        "📋 Copy prompt to clipboard",
        on_click=lambda: st.write(
            f"<script>navigator.clipboard.writeText({repr(copilot_prompt)})</script>",
            unsafe_allow_html=True,
        ),
        use_container_width=True,
    )
    col_b.link_button(
        "🌐 Open Copilot →",
        url="https://copilot.microsoft.com",
        use_container_width=True,
    )

    st.divider()
    st.markdown("#### What to ask Copilot")
    st.markdown("""
After pasting the prompt you can follow up with:
- *"Summarise this as 3 executive bullet points"*
- *"Which company should we benchmark ourselves against and why?"*
- *"Draft a PowerPoint slide title and subtitle for each metric"*
- *"Write a briefing note for our CEO on the top and bottom performers"*
- *"Suggest 5 strategic recommendations based on these results"*
""")

# ── Download ───────────────────────────────────────────────────────────────────
st.divider()
col1, col2 = st.columns([2, 1])
col1.download_button(
    label="📥 Download Excel Report (with Copilot prompt included)",
    data=excel_bytes,
    file_name="utility_benchmark.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)
col2.markdown(
    "The Excel file includes all 4 sheets plus the Copilot prompt as a "
    "ready-to-copy sheet."
)
