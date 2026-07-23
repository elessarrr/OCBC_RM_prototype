# Project Learnings

## Proactive Prevention (patterns we keep hitting)

*   **Always run from `wealth-brief/`:** uvicorn, pytest, and imports assume that cwd (not the repo root).
*   **API secrets in `.env` only:** put `DEEPSEEK_API_KEY` / `FINNHUB_API_KEY` in `wealth-brief/.env` or Railway vars — never commit keys; restart the server after editing `.env`.
*   **Treat LLM calls as unreliable I/O:** market snapshot must render even if DeepSeek fails; return a safe user message — never raw exception text. See `docs/solutions/best-practices/graceful-llm-degradation.md`.
*   **DeepSeek ProxyError 403 via Cursor/local proxy:** `HTTP_PROXY`/`HTTPS_PROXY` can block `api.deepseek.com`. Use `httpx.Client(trust_env=False)` on the OpenAI client, and for local uvicorn clear proxy env (`env -u http_proxy -u https_proxy …`) when starting from an agent shell. See `docs/solutions/runtime-errors/httpx-proxy-403-deepseek-finnhub-trust-env.md`.
*   **FastAPI `Form(...)` needs `python-multipart`:** any endpoint with `Form()` params (e.g. `POST /generate`) crashes at import on Railway with `RuntimeError: Form data requires "python-multipart"`. Keep `python-multipart` in `requirements.txt`. See `docs/solutions/build-errors/python-multipart-required-for-fastapi-form.md`.
*   **Finnhub timeout ≠ blank page:** use curated static headlines (≤ ~1 day old OK) when Finnhub errors.
*   **Refresh `fallback_headlines.py` before each demo:** the static fallback list is frozen at creation time; stale generic headlines are visible to interviewers if Finnhub is down. Update before high-stakes demos.
*   **Bump CSS `?v=N` on every style deploy:** `index.html` line 7 has a hardcoded version query string; increment it manually on any CSS-touching commit to prevent browser cache serving stale styles.
*   **Persona regenerate reuses snapshot:** `POST /generate` must not re-fetch yfinance by default — same numbers, different framing.
*   **Brand red ≠ loss red:** UI chrome `#e1241c`; down moves `#dc2626` + ↓ only inside snapshot cells.
*   **No hard max-token cap:** prompt for concise 2–3 paragraphs; allow enough tokens for a good answer.
*   **Paid Railway:** no free-tier sleep/warmup ritual required for demo.
*   **Pin ML deps (transformers/torch/sentence-transformers):** unpinned, a clean install drifts to a broken `transformers` 5.x (`torch` NameError at import); pin as a matched set and to a torch version with wheels on every platform you validate on. See `docs/solutions/build-errors/unpinned-ml-deps-broke-ci.md`.
*   **Independent judge for LLM eval:** never score LLM output with the same model that generated it; use a different (ideally larger) judge, warn if they match, and treat LLM-judge numbers as directional. See `docs/solutions/best-practices/independent-llm-judge-for-eval.md`.
*   **Trace user-visible outputs, not imports:** an imported engine/model does not prove the dashboard runs it; follow entrypoint → caller → returned data → rendered widget. See `docs/solutions/best-practices/verify-portfolio-claims-against-runtime-paths.md`.
*   **yfinance proxy 403 (curl_cffi CONNECT tunnel):** yfinance uses `curl_cffi` internally, which reads system proxy vars — completely independent of the httpx/openai client fix. Start uvicorn with `env -u http_proxy -u https_proxy …` to prevent all 8 tickers returning `—`. Railway containers are unaffected. See `docs/solutions/runtime-errors/yfinance-proxy-403-connect-tunnel.md`.
*   **HTMX indicator element must live outside its hx-target:** placing `#brief-loader` inside `#brief-region` means the first HTMX swap destroys it; subsequent `hx-indicator="#brief-loader"` references return no matches and show no spinner. See `docs/solutions/ui-bugs/htmx-indicator-destroyed-by-swap-target.md`.
*   **Use `<button type="button">` not `<span role="button">`:** native button elements are opaque ARIA leaf nodes; span+role creates ARIA containment that makes sibling element selectors ambiguous in automation tools. See `docs/solutions/ui-bugs/span-role-button-aria-tree-nesting.md`.
*   **`monkeypatch.delenv` for missing-key tests:** `load_dotenv()` at import time leaks `.env` into `os.environ`; tests asserting on absent API keys must use `monkeypatch.delenv("KEY", raising=False)`. See `docs/solutions/test-failures/dotenv-leaks-api-keys-into-pytest.md`.
*   **Clipboard controls need a synchronous fallback:** permission-restricted browsers may reject `navigator.clipboard`; attempt the textarea/`execCommand("copy")` fallback before awaiting the modern API. See `docs/solutions/ui-bugs/clipboard-api-permission-fallback.md`.
*   **Production fail-closed guards need matching CI env:** when Flask/Rails/etc. refuse boot without secrets, grep GitHub Actions and cron scripts — repo secrets alone are not enough without workflow `env` mapping. See `docs/solutions/integration-issues/ast-weekly-ingest-secret-key-github-actions.md`.
*   **GitHub Actions Re-run ≠ latest workflow:** "Re-run failed jobs" replays the original commit/YAML; use **Run workflow** on current `main` after fixing workflows. See `docs/solutions/workflow-issues/github-actions-rerun-stale-workflow-yaml.md`.

---

<!-- Numbered incident write-ups below as they occur. Format:

## N. Short title
*   **Date & Error:** ...
*   **Root Cause:** ...
*   **The Resolution:** ...
-->

## 1. gstack Cursor installer mismatch
*   **Date & Error:** 2026-07-18 — `./setup --host cursor` was rejected, then setup stopped because `bunx` was unavailable.
*   **Root Cause:** gstack 1.60.1.0 documents and implements Cursor skill generation, but its shell host allowlist omits Cursor; this Bun installation exposes `bun x` rather than a separate `bunx`.
*   **The Resolution:** Ran `bun x playwright install chromium`, completed standard setup, generated skills with `bun run gen:skill-docs:user --host cursor`, and linked the generated skills under `~/.cursor/skills/`. See `docs/solutions/build-errors/gstack-cursor-installer-host-mismatch.md`.

## 2. yfinance proxy 403 — all tickers return `—`
*   **Date & Error:** 2026-07-16 — `curl_cffi.curl.CurlError: Failed to perform, curl: (56) CONNECT tunnel failed, response 403` on every `yf.Ticker(...).history()` call.
*   **Root Cause:** yfinance uses `curl_cffi` which inherits system proxy env vars at session creation; a CONNECT-tunnel proxy blocking `*.yahoo.com` kills all ticker fetches. The `httpx.Client(trust_env=False)` fix for DeepSeek does not help here — different transport.
*   **The Resolution:** Start uvicorn with proxy env vars cleared: `env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY .venv/bin/uvicorn ...`. Railway production is unaffected. See `docs/solutions/runtime-errors/yfinance-proxy-403-connect-tunnel.md`.

## 3. HTMX `hx-indicator` destroyed by `hx-target` swap
*   **Date & Error:** 2026-07-18 — loading spinner only appeared on first generation; `hx-indicator="#brief-loader" returned no matches!` in browser console on all subsequent submits.
*   **Root Cause:** `#brief-loader` was nested inside `#brief-region` (the `hx-target`); `hx-swap="innerHTML"` replaced all of `#brief-region`'s children on first success, removing `#brief-loader` from the DOM.
*   **The Resolution:** Moved `#brief-loader` to be a sibling of `#brief-region` (outside the swap target) in `templates/index.html`. See `docs/solutions/ui-bugs/htmx-indicator-destroyed-by-swap-target.md`.

## 4. `<span role="button">` breaks ARIA tree and automation selectors
*   **Date & Error:** 2026-07-18 — browse tool `@ref` clicks on radio buttons raised "Selector matched multiple elements" after adding the sentiment ⓘ button as a span.
*   **Root Cause:** Chromium treats `<span role="button">` as an ARIA container; subsequent sibling elements (including the tooltip and form controls) are nesting-attributed as descendants, making ref-based selectors ambiguous.
*   **The Resolution:** Replaced with `<button type="button">` and added `role="tooltip"` to the nested span. See `docs/solutions/ui-bugs/span-role-button-aria-tree-nesting.md`.

## 5. `load_dotenv()` at import leaks `.env` API keys into pytest
*   **Date & Error:** 2026-07-18 — `test_generate_brief_without_api_key` gave false greens; `DEEPSEEK_API_KEY` was found in `os.environ` because `pytest` imported `main.py` which called `load_dotenv()` at module level.
*   **Root Cause:** `load_dotenv()` populates `os.environ` for the entire process; any test importing `main` (via `TestClient`) inherits all `.env` keys, silently defeating tests that expect them to be absent.
*   **The Resolution:** Added `monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)` to the test. See `docs/solutions/test-failures/dotenv-leaks-api-keys-into-pytest.md`.

## 6. Clipboard API denied in browser QA
*   **Date & Error:** 2026-07-19 — both Copy Brief and Copy Email displayed `Copy failed` in permission-restricted Chromium.
*   **Root Cause:** `navigator.clipboard.writeText()` was denied, and an asynchronous fallback would run after the click's transient user activation had expired.
*   **The Resolution:** Added a shared synchronous textarea/`document.execCommand("copy")` fallback in `wealth-brief/static/app.js`, then retained the Clipboard API as the secondary path. See `docs/solutions/ui-bugs/clipboard-api-permission-fallback.md`.

## 7. FastAPI Form import crash without python-multipart
*   **Date & Error:** 2026-07-17 — `RuntimeError: Form data requires "python-multipart" to be installed` on Railway import.
*   **Root Cause:** `POST /generate` uses `Form(...)` but `python-multipart` was not in `requirements.txt`.
*   **The Resolution:** Added `python-multipart>=0.0.9` to `wealth-brief/requirements.txt`. See `docs/solutions/build-errors/python-multipart-required-for-fastapi-form.md`.

## 8. DeepSeek and Finnhub blocked by local httpx proxy inheritance
*   **Date & Error:** 2026-07-16 — `httpx.ProxyError: 403 Forbidden` / `openai.APIConnectionError: Connection error.` despite valid keys; Finnhub logged `403 Forbidden` and fell back to static headlines.
*   **Root Cause:** httpx defaults to `trust_env=True`, routing through agent-shell proxy vars that block external APIs.
*   **The Resolution:** `httpx.Client(trust_env=False)` for DeepSeek; `httpx.get(..., trust_env=False)` for Finnhub. See `docs/solutions/runtime-errors/httpx-proxy-403-deepseek-finnhub-trust-env.md`.

## 9. AST weekly GitHub Actions ingest blocked by missing SECRET_KEY mapping
*   **Date & Error:** 2026-07-20 — `ValueError: No SECRET_KEY set for Flask application. This is required in production` at `flask db upgrade head` (Portfolio run #6).
*   **Root Cause:** Production SECRET_KEY fail-closed (`0118006`) plus `weekly-ingest.yml` missing `SECRET_KEY: ${{ secrets.AST_SECRET_KEY }}`.
*   **The Resolution:** Added GitHub secret and workflow env mapping on Portfolio `main` (`920770d`); triggered fresh workflow dispatch. See `docs/solutions/integration-issues/ast-weekly-ingest-secret-key-github-actions.md`.

## 10. GitHub Actions Re-run replayed stale workflow after fix
*   **Date & Error:** 2026-07-20 — Re-running failed ingest #6 kept the same SECRET_KEY error after fix landed on `main`.
*   **Root Cause:** Re-run uses the original run's commit SHA and workflow snapshot, not current `main`.
*   **The Resolution:** Use **Run workflow** on current `main` and verify run commit SHA. See `docs/solutions/workflow-issues/github-actions-rerun-stale-workflow-yaml.md`.
