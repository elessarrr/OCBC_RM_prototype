# Engineering Log & Knowledge Journal

> **Format (per AGENTS.md):** One entry per completed task / major bug / stack learning.  
> **1–2 sentences each.** Group by month; newest entry first within each month.

**App:** `wealth-brief/` · **PRD:** `tasks/0001-prd-wealth-market-brief-generator.md`  
**Local:** `uvicorn main:app --reload` from `wealth-brief/` (typical `http://127.0.0.1:8000`)

---

## July 2026 (newest first)

- **2026-07-17** — *Railway build fix.* Deploy crashed on import: FastAPI `Form(...)` on `/generate` needs `python-multipart`; added to `requirements.txt`. See `LEARNINGS.md`.
- **2026-07-16** — *Headline links + count.* Finnhub items now keep article URLs; UI shows up to 10 linked headlines plus Finnhub attribution; tests green.
- **2026-07-16** — *DeepSeek proxy 403 fixed.* Local brief failed with `httpx.ProxyError: 403` despite a valid key; `httpx.Client(trust_env=False)` + starting uvicorn without proxy env vars restored live briefs.
- **2026-07-16** — *LLM swap to DeepSeek.* Replaced Anthropic Claude with `deepseek-chat` via OpenAI-compatible client (`DEEPSEEK_API_KEY`); 19 tests green. Railway/local must set the new env var name — Finnhub still optional (static fallback).
- **2026-07-14** — *GitHub remote created.* Installed `gh`, authenticated as elessarrr, pushed `main` to https://github.com/elessarrr/OCBC_RM_prototype (public). Next: Railway Root Directory `wealth-brief` + API env vars.
- **2026-07-13** — *Agent infra bootstrap.* Customized `AGENTS.md` for Wealth Morning Brief; added `JOURNAL.md`, `LEARNINGS.md`, `CONCEPTS.md`, `.compound/` + `docs/solutions/`, context snapshot, and compound cheat sheet (patterned on Aircraft Safety Tracker, without aviation/gstack). Ready for autonomous task-list implementation.
