# con-ed
Benchmarking Tool
This is a well-scoped project. Here's a complete implementation — architecture first, then all the code.

System architecture
The platform has seven modular components in a clean pipeline:
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation-duration: 0.25s;
    animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1);
  }
VvisualizeVvisualize show_widget
Implementation plan
The build follows 7 sequential phases: (1) project scaffold and config, (2) input handler, (3) data collector with scraping + API fallback, (4) AI-assisted extractor using simulated LLM calls, (5) cleaner and normalizer using pandas, (6) benchmark engine for rankings and stats, and (7) output generator writing the 3-sheet Excel workbook plus insight text. The Streamlit UI ties everything together as an orchestration layer.

How each part works
config.py is the single source of truth for defaults and metric synonyms. Adding a new metric requires only one edit here — no module code changes.
input_handler.py normalizes whitespace and deduplicates before anything else runs, so "Con  Edison" and "con edison" are never treated as different companies.
data_collector.py tries a live DuckDuckGo search scrape first, then falls back to the SIMULATED_DATA dict. Because the fallback is deterministic (same input → same text), the prototype is fully reproducible even without internet access.
ai_extractor.py has two backends behind the same interface. The rule-based backend uses METRIC_SYNONYMS from config plus a regex that handles units like "billion", "%", and "minutes" — no LLM needed for the demo. Swapping in OpenAI requires only setting OPENAI_API_KEY.
data_cleaner.py converts raw strings like "$15.7 billion" → 15_700_000_000.0 via scale-word detection, then pivots into a companies × metrics matrix. Missing values are imputed with the column mean.
benchmark_engine.py knows which metrics are "lower is better" (outages, emissions) and which are "higher is better", so rank 1 always means best regardless of direction. Percentiles follow the same inversion logic.
output_generator.py writes all three sheets with styled headers, alternating row shading, and auto-fit columns. The function returns bytes so Streamlit can stream it directly to the download button without writing to disk.
app.py is purely orchestration and display — it contains no business logic, making it easy to replace Streamlit with a FastAPI endpoint or a CLI later.
