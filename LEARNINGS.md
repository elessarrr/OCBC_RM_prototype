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

---

<!-- Numbered incident write-ups below as they occur. Format:

## N. Short title
*   **Date & Error:** ...
*   **Root Cause:** ...
*   **The Resolution:** ...
-->
