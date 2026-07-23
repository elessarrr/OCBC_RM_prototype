# Wealth Morning Brief

A FastAPI prototype that gives wealth relationship managers a personalised AI-generated morning brief alongside live market data — generic on page load, persona-aware when the RM selects a client profile.

**Live demo:** https://ocbcrmprototype-production.up.railway.app

---

## What it does

The RM opens the page and immediately sees eight live market series (STI, S&P 500, Hang Seng, Nikkei, USD/SGD, Gold, Brent, US 10Y Yield), a derived sentiment score, and a filtered news feed — all fetched from public APIs on page load.

A DeepSeek brief generates automatically. Selecting a client profile (wealth tier, goal, geography, asset focus) regenerates the brief with persona-aware framing from the same live snapshot — same numbers, different emphasis and tone.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + Jinja2 + HTMX (server-rendered, no SPA) |
| Market data | yfinance — 8 series + VIX/S&P inputs for sentiment |
| News | Finnhub REST with financial keyword filter; static fallback |
| LLM | DeepSeek `deepseek-chat` via OpenAI-compatible API |
| Deploy | Railway (paid, always-on) |

---

## A few decisions worth explaining

**One LLM call, four sections.** A structured plain-text contract (`BRIEF:`, `INVESTMENT_IDEAS:`, `WATCH:`, `HOUSE_VIEW:`) extracts four panels from a single DeepSeek completion. Missing sections degrade to empty panels; a missing `BRIEF` or any exception returns a safe fallback message rather than an error page.

**Snapshot reuse on persona regenerate.** The app reuses the in-page snapshot on regenerate rather than refetching yfinance. The brief changes; the numbers stay consistent with what was displayed.

**Hidden form fields for market payload.** The market snapshot and headlines are fetched once on page load, serialised as JSON into hidden form fields, and re-posted on Generate. This keeps the brief grounded on the data the RM actually saw and lets the server stay stateless — no session store, no Redis, no second market-API round-trip.

**Graceful degradation throughout.** Finnhub failure → curated static headlines. Per-ticker yfinance failure → that cell shows `—`, page continues. DeepSeek failure → safe message, market snapshot still visible.

---

## Prototype scope

Generated investment ideas and house views are labelled *demo* and *simulated*. A persistent footer states this is not official OCBC research or advice.

A production path would replace open-ended generation with governed retrieval from bank-approved research: ingest proprietary documents with access controls and expiry metadata, retrieve only current authorised passages per RM and client context, generate with source citations, and log the full chain for audit.

---

## Running locally

```bash
cd wealth-brief
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill DEEPSEEK_API_KEY and FINNHUB_API_KEY
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

---

## Tests

```bash
cd wealth-brief && pytest -q   # 44 tests
```

See [`wealth-brief/README.md`](wealth-brief/README.md) for endpoint reference, demo walkthrough, and Railway deploy notes.
