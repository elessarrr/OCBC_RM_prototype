# Project Learnings

## Proactive Prevention (patterns we keep hitting)

*   **Always run from `wealth-brief/`:** uvicorn, pytest, and imports assume that cwd (not the repo root).
*   **API secrets in `.env` only:** put `ANTHROPIC_API_KEY` / `FINNHUB_API_KEY` in `wealth-brief/.env` or Railway vars — never commit keys; restart the server after editing `.env`.
*   **Treat LLM calls as unreliable I/O:** market snapshot must render even if Claude fails; return a safe user message — never raw exception text. See `docs/solutions/best-practices/graceful-llm-degradation.md`.
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
