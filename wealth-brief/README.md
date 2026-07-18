# Wealth Morning Brief

AI Lab interview prototype: a single-page FastAPI app that pulls live (or last-close) market data, headlines, and a DeepSeek morning brief for wealth RMs — generic on load (V1), persona-aware on regenerate (V2).

**One-line pitch:** The content layer that makes OCBC WoW-style hyper-personalisation feel specific, not generic.

**Live demo:** https://ocbcrmprototype-production.up.railway.app

**PRD:** [`tasks/0001-prd-wealth-market-brief-generator.md`](../tasks/0001-prd-wealth-market-brief-generator.md)

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + Jinja2 + HTMX |
| Markets | yfinance (7 series) |
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
2. Fill **Client Profile** (tier / goal / ≤2 asset classes / geography) → **Generate My Brief**.
3. Switch persona and regenerate: **same numbers**, different framing + badge.
4. Copy button copies the brief text.

Graceful degradation is intentional: Finnhub or DeepSeek failures must never blank the snapshot.

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
