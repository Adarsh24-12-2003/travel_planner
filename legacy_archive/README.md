# Session 18 Practical Kit — Project Refactor Day (LangGraph Travel Planner)

This kit is designed for **Session 18** of Module 6: **Project Refactor Day**.
You will take a travel planner agent and make it **production-grade** by adding:

- **Error retries** (bounded attempts + exponential backoff)
- **Exception guards** (validate inputs/outputs, avoid crashes, graceful fallbacks)
- **Failure routing** in a **LangGraph** state machine
- Basic **observability** (structured logs) and **tests**

## 0) What runs without paid APIs?
By default the project uses **Ollama (local)** via `ChatOllama`.
No paid APIs are required.

If you *want* to use OpenAI later, see the notes in `src/llm.py`.


## Optional: Switch to OpenAI
If you want to use OpenAI instead of Ollama:

1) Ensure the extra deps are installed (already included in requirements.txt in this kit):
```bash
pip install -r requirements.txt
```
2) Set in `.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=YOUR_KEY
OPENAI_MODEL=gpt-4o-mini
```
3) Run the CLI command as usual.

Cost note: the code is designed to keep LLM calls minimal (tools generate most structure), so token usage stays low.

## 1) Prerequisites
- Python **3.10+** (recommended: **3.11**)
- Ollama installed (optional but recommended for default mode)
  - Install: https://ollama.com
  - Pull a model (example): `ollama pull llama3.1`

## 2) Setup
```bash
cd session18_practical_kit
python -m venv .venv
# mac/linux:
source .venv/bin/activate
# windows:
# .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

## 3) Run the refactored travel planner (CLI)
```bash
python -m src.main --from "Mumbai" --to "Goa" --start "2026-03-10" --days 4 --budget_inr 35000
```

## 4) What you should modify during the workshop
Open `src/config.py` and try toggling:
- `SIMULATE_TRANSIENT_FAILURES=True` to see retries in action
- `MAX_RETRIES` and backoff settings

Tip: you can also set these in `.env` (no code edits needed):
- `SIMULATE_TRANSIENT_FAILURES=true|false`
- `TRANSIENT_FAILURE_RATE=0.25`

Then open `src/nodes.py` and implement/refine:
- guards: missing fields, invalid dates, unrealistic budgets
- fallbacks: if flights fail after retries, switch to “approximate options”
- loop exit criteria: “critique score >= threshold” or “max revisions reached”

## 5) Run tests
```bash
pytest -q
```

If you ever see `ModuleNotFoundError: No module named 'src'`, make sure you're running `pytest` from the
`session18_practical_kit/` folder (project root).

## Project structure
- `src/config.py` — workshop knobs (retries + failure simulation; supports env overrides)
- `src/state.py` — strongly-typed shared state + validation helpers
- `src/retry.py` — retry policy (no external dependency)
- `src/guards.py` — exception guards and safe-call helpers
- `src/tools.py` — offline tools (flights/hotels/itinerary) + failure simulation
- `src/llm.py` — LLM wrapper (default: Ollama)
- `src/nodes.py` — graph nodes (research → plan → critique → revise)
- `src/graph.py` — LangGraph state machine wiring + failure routing
- `src/main.py` — CLI entrypoint
- `tests/` — unit tests for retry + guards + graph behavior

## Learning targets (tie back to Session 18)
- Add **retries** where errors are transient (timeouts, rate limits).
- Add **guards** where errors are preventable (bad inputs, schema mismatch).
- Route failures to **fallback nodes** instead of crashing.


## 2) Notebooks included (BEFORE vs AFTER)

This kit includes notebooks so the "refactor" is crystal clear:

- `baseline/travel_planner.ipynb` — **BEFORE** (prototype / happy path)
- `travel_planner_refactor_workshop.ipynb` — **AFTER** walkthrough
  - Uses the same refactor utilities from `src/` (guards, retries, failure routing)
  - Includes 3 run scenarios to demonstrate robustness

### Suggested classroom flow (3 hours)
1. Run the **baseline** notebook and intentionally trigger failures (missing fields, simulated tool failures).
2. Switch to the **workshop** notebook and implement/inspect:
   - typed state
   - safe_call guards
   - retry policy
   - fallback edges
3. Validate with the 3 scenarios at the end of the workshop notebook.
