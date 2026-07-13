# Tasks: Personalised Wealth Market Brief Generator

**PRD:** `tasks/0001-prd-wealth-market-brief-generator.md`  
**Status:** Ready for implementation

## Relevant Files

- `wealth-brief/main.py` — FastAPI app: `GET /`, `POST /generate`, `GET /market`, optional `GET /health`; wires templates and services.
- `wealth-brief/data/market.py` — yfinance fetch for 7 series + Finnhub news + static headline fallback; `"as of"` timestamp (SGT).
- `wealth-brief/data/fallback_headlines.py` — Curated static headlines (≤ ~1 day old when frozen) used when Finnhub fails.
- `wealth-brief/llm/brief.py` — Prompt construction (V1 + V2 append) + Anthropic Claude call; graceful user-safe errors; no hard max-token cap.
- `wealth-brief/templates/index.html` — Single-page Jinja2 UI (snapshot, headlines, brief, V2 form, HTMX).
- `wealth-brief/templates/partials/brief.html` — HTMX partial for brief narrative + persona badge (returned by `/generate`).
- `wealth-brief/static/style.css` — OCBC red/white colour system; spinner; mobile layout.
- `wealth-brief/static/app.js` — Brief auto-load / 15s secondary loading copy; copy-to-clipboard; asset multi-select max-2 (if not done in HTMX alone).
- `wealth-brief/requirements.txt` — fastapi, uvicorn, jinja2, python-dotenv, yfinance, httpx, anthropic, gunicorn (Railway).
- `wealth-brief/.env.example` — `ANTHROPIC_API_KEY`, `FINNHUB_API_KEY` (names only).
- `wealth-brief/.env` — Local secrets (gitignored).
- `wealth-brief/.gitignore` — Ignore `.env`, `__pycache__`, `.venv`, etc.
- `wealth-brief/Procfile` — Railway web process (e.g. gunicorn/uvicorn).
- `wealth-brief/README.md` — What it is, why, how to run, env vars, demo notes.
- `wealth-brief/tests/test_market.py` — Unit tests for series parsing, last-close behaviour, Finnhub fallback.
- `wealth-brief/tests/test_brief.py` — Unit tests for prompt construction (V1/V2) and graceful LLM failure (mocked client).
- `wealth-brief/tests/test_routes.py` — API tests for `/`, `/market`, `/generate`, `/health` with mocks.

### Notes

- Greenfield: create the `wealth-brief/` tree from scratch; do not invent OCBC logos or navy theme.
- Prefer `pytest` for Python tests (not Jest). From `wealth-brief/`: `pytest` or `pytest tests/test_market.py`.
- Secrets only in `.env` / Railway variables — never commit keys.
- V1 before V2: snapshot must always render even if Claude/Finnhub fail (Aircraft Safety Tracker–style graceful degradation).
- Persona regenerate reuses the **current in-page snapshot**; do not re-fetch yfinance on `POST /generate` unless explicitly refreshing markets.
- Prompt still asks for concise 2–3 plain paragraphs; **no hard max-token cap**.
- Paid Railway: `/health` is optional; no demo-day warmup ritual required.

## Tasks

- [x] 1.0 Scaffold FastAPI project structure, dependencies, and secrets config
  - [x] 1.1 Create `wealth-brief/` directory layout per PRD (`main.py`, `data/`, `llm/`, `templates/`, `static/`, `tests/`)
  - [x] 1.2 Add `requirements.txt` with FastAPI, uvicorn/gunicorn, Jinja2, python-dotenv, yfinance, httpx, anthropic, pytest
  - [x] 1.3 Add `.gitignore` and `.env.example` (`ANTHROPIC_API_KEY`, `FINNHUB_API_KEY`); create local `.env` (untracked)
  - [x] 1.4 Stub `main.py` with FastAPI app, Jinja2Templates, StaticFiles mount, and a placeholder `GET /` that renders a minimal page
  - [x] 1.5 Add `Procfile` for Railway and confirm app starts locally (`uvicorn main:app --reload`)

- [x] 2.0 Implement market data (yfinance) and news (Finnhub + static fallback)
  - [x] 2.1 Implement `fetch_market_snapshot()` in `data/market.py` for all 7 symbols (`^STI`, `^GSPC`, `^HSI`, `^N225`, `USDSGD=X`, `GC=F`, `BZ=F`) with price, point change, % change, arrow (↑ ↓ →)
  - [x] 2.2 Attach `"as of"` timestamp in SGT; on closed market / weekend return **last close** (never blank or invented)
  - [x] 2.3 Implement Finnhub fetch (general + forex); normalise to a short headline list (target ≥ 3 for display)
  - [x] 2.4 Curate and freeze `fallback_headlines.py` from a real Finnhub pull (≤ ~1 day old OK); use on timeout/error
  - [x] 2.5 Write `tests/test_market.py` covering happy path (mocked), fallback path, and snapshot shape

- [ ] 3.0 Build V1 page: market snapshot UI, auto Claude brief, graceful degradation
  - [ ] 3.1 Build `index.html` + `style.css`: header, MARKET SNAPSHOT grid, TOP HEADLINES, TODAY'S BRIEF region (OCBC red/white; loss red `#dc2626` only on ↓)
  - [ ] 3.2 Wire `GET /` to load snapshot + headlines server-side and render immediately (FR-1–4)
  - [ ] 3.3 Implement `llm/brief.py` with PRD V1 system/user prompts; Claude `claude-sonnet-4-6`; temperature 0.4; no hard max-token cap; plain text only
  - [ ] 3.4 On LLM auth/network/API failure, return safe user message (e.g. "Brief temporarily unavailable…"); never expose exception text or keys (FR-7)
  - [ ] 3.5 Auto-generate brief on page load (HTMX or fetch into brief region) with red spinner + "Generating your brief…"; after 15s show secondary "This is taking a moment…" (FR-5, FR-8)
  - [ ] 3.6 Ensure snapshot never waits on Claude — brief section loads independently (FR-7)
  - [ ] 3.7 Write `tests/test_brief.py` for prompt payload construction and mocked failure → safe message

- [ ] 4.0 Add `/market` (and optional `/health`), polish V1 CSS, deploy to Railway
  - [ ] 4.1 Implement `GET /market` JSON endpoint returning 7 series + timestamp (FR-9); optional refresh control on UI
  - [ ] 4.2 Optional: implement `GET /health` with no external API calls (FR-10)
  - [ ] 4.3 Mobile-responsive polish; title "Wealth Morning Brief — AI Lab Prototype"; no OCBC logo (FR-18, FR-19)
  - [ ] 4.4 Set Railway env vars; deploy; verify public URL shows snapshot + brief or safe fallback
  - [ ] 4.5 Smoke-test on phone; confirm V1 DoD (FR-1–9, optional FR-10)

- [ ] 5.0 Implement V2 client profile form, persona-aware `/generate`, and badge
  - [ ] 5.1 Add CLIENT PROFILE form: wealth tier, primary goal, asset focus (multi-select max 2), geography (single); completable in < 30s (FR-11)
  - [ ] 5.2 Implement `POST /generate` accepting profile + **current snapshot from client** (or server-held page state); do **not** re-fetch yfinance by default (FR-12)
  - [ ] 5.3 Append V2 system-prompt block (tier/goal/assets/geography guidance) in `brief.py` (FR-13)
  - [ ] 5.4 Return HTMX partial with narrative + persona badge (e.g. `Capital Preservation | HNW | Singapore Focus`) (FR-14)
  - [ ] 5.5 Manually verify ≥ 3 persona combos produce meaningfully different briefs from identical market data (FR-15); tune prompts if needed
  - [ ] 5.6 Extend `tests/test_brief.py` / `tests/test_routes.py` for V2 prompt contents and `/generate` behaviour with mocks

- [ ] 6.0 Polish for demo: copy button, persona differentiation check, README, stress test
  - [ ] 6.1 Add Copy button for brief text (clipboard) (FR-16)
  - [ ] 6.2 Stress test: 10 consecutive generations; Finnhub fallback path verified; no raw errors in UI
  - [ ] 6.3 Write `README.md` (purpose, stack, env setup, local run, Railway notes, link to PRD)
  - [ ] 6.4 Run full demo narrative 3× (V1 auto-brief → two persona switches); fix clunk
  - [ ] 6.5 Final checklist: FR-1–19 (FR-10 optional); secrets not in git; public URL stable
