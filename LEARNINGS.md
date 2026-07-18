# Project Learnings

## Proactive Prevention (patterns we keep hitting)

*   **Always run from `wealth-brief/`:** uvicorn, pytest, and imports assume that cwd (not the repo root).
*   **API secrets in `.env` only:** put `DEEPSEEK_API_KEY` / `FINNHUB_API_KEY` in `wealth-brief/.env` or Railway vars — never commit keys; restart the server after editing `.env`.
*   **Treat LLM calls as unreliable I/O:** market snapshot must render even if DeepSeek fails; return a safe user message — never raw exception text. See `docs/solutions/best-practices/graceful-llm-degradation.md`.
*   **DeepSeek ProxyError 403 via Cursor/local proxy:** `HTTP_PROXY`/`HTTPS_PROXY` can block `api.deepseek.com`. Use `httpx.Client(trust_env=False)` on the OpenAI client, and for local uvicorn clear proxy env (`env -u http_proxy -u https_proxy …`) when starting from an agent shell.
*   **FastAPI `Form(...)` needs `python-multipart`:** any endpoint with `Form()` params (e.g. `POST /generate`) crashes at import on Railway with `RuntimeError: Form data requires "python-multipart"`. Keep `python-multipart` in `requirements.txt`.
*   **Finnhub timeout ≠ blank page:** use curated static headlines (≤ ~1 day old OK) when Finnhub errors.
*   **Persona regenerate reuses snapshot:** `POST /generate` must not re-fetch yfinance by default — same numbers, different framing.
*   **Brand red ≠ loss red:** UI chrome `#e1241c`; down moves `#dc2626` + ↓ only inside snapshot cells.
*   **No hard max-token cap:** prompt for concise 2–3 paragraphs; allow enough tokens for a good answer.
*   **Paid Railway:** no free-tier sleep/warmup ritual required for demo.
*   **Pin ML deps (transformers/torch/sentence-transformers):** unpinned, a clean install drifts to a broken `transformers` 5.x (`torch` NameError at import); pin as a matched set and to a torch version with wheels on every platform you validate on. See `docs/solutions/build-errors/unpinned-ml-deps-broke-ci.md`.
*   **Independent judge for LLM eval:** never score LLM output with the same model that generated it; use a different (ideally larger) judge, warn if they match, and treat LLM-judge numbers as directional. See `docs/solutions/best-practices/independent-llm-judge-for-eval.md`.
*   **gstack Cursor setup mismatch:** the README may list `--host cursor` while the shell installer rejects it; use the Cursor document generator and link its generated skills. See `docs/solutions/build-errors/gstack-cursor-installer-host-mismatch.md`.

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
*   **The Resolution:** Ran `bun x playwright install chromium`, completed standard setup, generated skills with `bun run gen:skill-docs:user --host cursor`, and linked the generated skills under `~/.cursor/skills/`.
