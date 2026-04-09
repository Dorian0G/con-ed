# Setup & Run Instructions

## 1. Prerequisites
- Python 3.11+ recommended
- `git` (optional, for cloning)

## 2. Create project directory
```bash
mkdir benchmark_tool && cd benchmark_tool
```
Copy all module files into the structure shown in the project layout artifact.
Create an empty `modules/__init__.py` file.

## 3. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

## 4. Install dependencies
```bash
pip install -r requirements.txt
```

## 5. (Optional) Enable real LLM extraction
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="sk-..."   # macOS / Linux
set OPENAI_API_KEY=sk-...        # Windows cmd
```
If unset, the tool runs entirely offline using the rule-based extractor
and simulated company data — fully functional for demo purposes.

## 6. Run the app
```bash
streamlit run app.py
```
The browser will open automatically at `http://localhost:8501`.

## 7. Use the tool
1. Enter company names in the sidebar (one per line).
2. Enter metric names (one per line).
3. Click **Generate Benchmark**.
4. Explore results across the four tabs.
5. Click **Download Excel Report** to get the formatted workbook.

---

## Adding new companies (simulated data)
Edit `modules/data_collector.py` → `SIMULATED_DATA` dict.
Add a new key (lowercase company name) with a text blob containing metric mentions.

## Adding new metrics
Edit `config.py` → `METRIC_SYNONYMS` dict.
Add a new key (canonical metric name) with a list of synonyms.
The extractor and benchmark engine will pick it up automatically.

## Running with real scraping (no simulated data)
The `collect_for_company()` function tries live scraping first.
Scraped content is passed to the extractor — LLM mode works best here
since real web pages are noisier than simulated text.

## Running headless (no UI)
```python
from modules.input_handler import parse_input
from modules.data_collector import collect_all
from modules.ai_extractor import extract_metrics
from modules.data_cleaner import build_raw_df, build_clean_df, fill_missing
from modules.benchmark_engine import build_benchmark
from modules.insight_generator import generate_insights
from modules.output_generator import save_excel

req = parse_input(["Con Edison", "Duke Energy"], ["Revenue", "Renewable Energy %"])
docs = collect_all(req.companies)
extracted = extract_metrics(docs, req.metrics)
raw_df = build_raw_df(extracted)
clean_df = fill_missing(build_clean_df(raw_df))
bench_df = build_benchmark(clean_df)
insights = generate_insights(bench_df)
save_excel(raw_df, clean_df, bench_df, insights, path="outputs/benchmark.xlsx")
```
