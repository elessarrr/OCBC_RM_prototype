# Engineering Log & Knowledge Journal

> **Format (per AGENTS.md):** One entry per completed task / major bug / stack learning.  
> **1–2 sentences each.** Group by month; newest entry first within each month.

**App:** `wealth-brief/` · **PRD:** `tasks/0001-prd-wealth-market-brief-generator.md`  
**Local:** `uvicorn main:app --reload` from `wealth-brief/` (typical `http://127.0.0.1:8000`)

---

## July 2026 (newest first)

- **2026-07-18** — *Demo enhancements: A3 + A1 + RM buttons.* Added US 10Y Yield (`^TNX`) to market snapshot (8 series), a Fear & Greed sentiment bar (VIX 60% + S&P 10-day momentum 40%, 0–100 scale, gradient bar with needle + ⓘ tooltip), RM contact buttons (Call + Message) in the brief partial, and reordered page so Today's Brief appears first. 27/27 tests green.
- **2026-07-18** — *Task 6.0 done (demo polish).* README + live URL; 10/10 stress generations with Finnhub fallback verified; demo narrative run 3× on Railway (V1 + two personas); `.env` not tracked. PRD task list **complete**.
- **2026-07-18** — *Task 5.0 done (V2 persona).* Added Client Profile form (tier/goal/assets≤2/geography) with HTMX regenerate that reuses in-page snapshot; FR-15 live check: 3 personas from identical data differed (jaccard ~0.23–0.25). **22 tests** green.
- **2026-07-18** — *Task 4.0 done (V1 deploy).* Mobile-responsive CSS polish; Railway project `soothing-reverence` verified live at `https://ocbcrmprototype-production.up.railway.app` with DeepSeek/Finnhub env vars; phone smoke + FR-1–10 DoD passed. Isolated `test_generate_brief_without_api_key` from local `.env` leakage.
- **2026-07-18** — *Ports/AST code-grounded Q&A.* Documented Ports file/cache/session-state data flow, the actual LinearRegression forecast UI path, scenario multipliers, Streamlit rerun and file-watcher mechanics, repo hygiene, and AST’s aggregate-only DeepSeek summary; corrected over-attribution and added honest scope language to the Ports README.
- **2026-07-18** — *RAG Learning Q&A + README honesty.* Extended `OCBC_AI_Lab_Interview_Prep.md` with FastAPI role, DuckDB↔Retriever arrows, eval harness (offline vs live path), all 19 judge questions (original 5 marked), brute-force vs indexed ANN (HNSW/IVF ELI5), embedding≠DB-write walkthrough, and a concrete definition of safety-first mutation. Corrected Bookmarks RAG README draft (DuckDB linear-scan; robots wording deferred to credibility PRD). Wrote `Planning/0003-prd-portfolio-credibility-hardening.md` in Bookmarks RAG (robots + stream test + `llama3.2:3b` default + Docker UI bonus).
- **2026-07-18** — *AST learning Q&A.* Expanded `OCBC_AI_Lab_Interview_Prep.md` with code-grounded answers on databases/SQLAlchemy, mutation safety, summary-thread concurrency, secret/empty-state risks, coverage and ASN fixture tests, precision/recall, null-fatality dedupe, link validation, fuzzy search and GitHub-Actions→Railway ingestion. Corrected overstatements: mutation safety is recurring but not universal, ASN listing parsing has fixture coverage, and threads are concurrent but unmanaged.
- **2026-07-17** — *Interview-prep repos hardened (external).* Fixed Bookmarks-RAG CI (unpinned ML deps drifted to a broken `transformers` 5.x → `torch` NameError; pinned the stack, added `requirements-dev.txt`, advisory lint/type + pytest hard gate) and added an independent RAGAS judge model + 19-question eval dataset. Both learnings captured in `docs/solutions/` (`build-errors/unpinned-ml-deps-broke-ci.md`, `best-practices/independent-llm-judge-for-eval.md`).
- **2026-07-17** — *Prep doc walk-back.* Updated `OCBC_AI_Lab_Interview_Prep.md` §9/§10 (+ consistency in §4/§5/§6/§8) now that AST CI/CD and RAG chunking-comparison are merged to `main` and RAG eval-rigor is an open, CI-green PR — claims are code-backed, so the "manage expectations" framing was softened accordingly.
- **2026-07-17** — *Railway build fix.* Deploy crashed on import: FastAPI `Form(...)` on `/generate` needs `python-multipart`; added to `requirements.txt`. See `LEARNINGS.md`.
- **2026-07-16** — *Headline links + count.* Finnhub items now keep article URLs; UI shows up to 10 linked headlines plus Finnhub attribution; tests green.
- **2026-07-16** — *DeepSeek proxy 403 fixed.* Local brief failed with `httpx.ProxyError: 403` despite a valid key; `httpx.Client(trust_env=False)` + starting uvicorn without proxy env vars restored live briefs.
- **2026-07-16** — *LLM swap to DeepSeek.* Replaced Anthropic Claude with `deepseek-chat` via OpenAI-compatible client (`DEEPSEEK_API_KEY`); 19 tests green. Railway/local must set the new env var name — Finnhub still optional (static fallback).
- **2026-07-14** — *GitHub remote created.* Installed `gh`, authenticated as elessarrr, pushed `main` to https://github.com/elessarrr/OCBC_RM_prototype (public). Next: Railway Root Directory `wealth-brief` + API env vars.
- **2026-07-13** — *Agent infra bootstrap.* Customized `AGENTS.md` for Wealth Morning Brief; added `JOURNAL.md`, `LEARNINGS.md`, `CONCEPTS.md`, `.compound/` + `docs/solutions/`, context snapshot, and compound cheat sheet (patterned on Aircraft Safety Tracker, without aviation/gstack). Ready for autonomous task-list implementation.
