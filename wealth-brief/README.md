# Wealth Morning Brief

AI Lab interview prototype: a single-page FastAPI app that pulls live (or last-close) market data, headlines, and a DeepSeek morning brief for wealth RMs — generic on load (V1), persona-aware on regenerate (V2).

**One-line pitch:** The content layer that makes OCBC WoW-style hyper-personalisation feel specific, not generic.

**Live demo:** https://ocbcrmprototype-production.up.railway.app

**PRDs:** [Core generator](../tasks/0001-prd-wealth-market-brief-generator.md) · [WoW-aligned demo enhancements](../tasks/0002-prd-wow-aligned-demo-enhancements.md)

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + Jinja2 + HTMX |
| Markets | yfinance (8 series) |
| News | Finnhub REST + static headline fallback |
| LLM | DeepSeek `deepseek-chat` (OpenAI-compatible API) |
| Deploy | Railway (paid), root directory `wealth-brief` |

## Local setup

```bash
cd wealth-brief
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill DEEPSEEK_API_KEY and FINNHUB_API_KEY
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

### Environment variables

| Name | Required | Notes |
|---|---|---|
| `DEEPSEEK_API_KEY` | Yes for live briefs | Without it, snapshot still renders; brief shows a safe fallback message |
| `FINNHUB_API_KEY` | Optional | Without it / on error, curated static headlines are used |

Never commit `.env`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Page + snapshot + headlines; auto-starts V1 brief |
| `POST` | `/generate` | Brief from **posted** snapshot/headlines (+ optional client profile). Does **not** re-fetch yfinance by default |
| `GET` | `/market` | JSON snapshot refresh |
| `GET` | `/health` | Cheap liveness (`{"status":"ok"}`) — no external calls |

## Demo notes

1. Open the page — market snapshot paints first; brief spinner then narrative (or safe fallback).
2. Select a persona chip, optionally edit the profile and portfolio mix, then press **Generate My Brief**.
3. Review the grounded brief, demo investment ideas, three-item watchlist, and explicitly simulated research view.
4. Switch persona and regenerate: **same numbers**, different framing + badge.

The fixed client-email draft helper remains in code (`SHOW_CLIENT_EMAIL_DRAFT` in `main.py`) but is UI-disabled so the page reads as a morning brief rather than an RM-only workflow.

Graceful degradation is intentional: Finnhub or DeepSeek failures must never blank the snapshot.

DeepSeek returns the brief, ideas, watchlist, and simulated research view in one structured plain-text response. A separate WATCH call is a fallback only if production evaluation shows that the one-call output is not reliable enough.

### Production research path (V3)

The prototype uses public market data and AI-generated demonstration content. It does not present official OCBC research, advice, or recommendations.

A production version can restrict generation to bank-approved proprietary research:

1. Ingest approved research documents with source, owner, publication date, jurisdiction, and expiry metadata.
2. Parse and chunk documents while preserving citations and access controls.
3. Index approved chunks in a permission-aware retrieval store.
4. Retrieve only current, authorised passages for the RM and client context.
5. Generate from those passages with source citations; refuse unsupported claims.
6. Log retrieved sources, prompt version, model version, and final output for audit.

**Interviewer one-liner:** “Today this demonstrates the RM content workflow; V3 replaces open-ended generation with governed retrieval from bank-approved research.”

### UI copy audit

Before a demo or release:

- Reject positive claims such as “OCBC recommends”, “official OCBC view”, or “OCBC advice”.
- Label generated ideas as **demo** and generated house views as **simulated** and **not official OCBC research**.
- Keep the persistent prototype/non-advice footer visible.
- Describe the production research path as a future governed capability, not a current integration.

## Tests

```bash
cd wealth-brief
source .venv/bin/activate
pytest -q
```

## Railway

- Project linked to this repo with **Root Directory** `wealth-brief`
- Procfile: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set `DEEPSEEK_API_KEY` and `FINNHUB_API_KEY` in Railway variables
