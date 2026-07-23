"""Wealth Morning Brief — the web app's front door.

Who does what (non-technical overview):
  - This file wires the browser to data fetching and AI brief generation.
  - The RM sees one page: market snapshot, headlines, client profile form, brief panel.
  - We do NOT ask the RM to paste prices or news — the app fetches and carries them forward.

Three main routes:
  GET  /         — load the page (fetch live data, render HTML)
  POST /generate — build the AI brief from data already on the page + optional profile
  GET  /health   — simple "is the server up?" check (used by Railway deploy)

Data flow for headlines (common interview question):
  fetch_headlines() on page load → Python list
  → json.dumps() embedded in hidden form field "headlines_json"
  → browser re-posts it on Generate (via HTMX)
  → json.loads() here in POST /generate → passed to llm/brief.py as "headlines"
  (brief.py never imports headlines — it receives them as a function argument)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from data.market import compute_sentiment, fetch_headlines, fetch_market_snapshot
from llm.brief import generate_brief

# Folder this file lives in — used to find templates, static CSS/JS, and .env secrets.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # Loads DEEPSEEK_API_KEY, FINNHUB_API_KEY from local .env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SGT = ZoneInfo("Asia/Singapore")  # Page date shown in Singapore time.

# Demo toggle: when True, the brief panel can show a pre-filled client email draft.
# Off by default so the page reads as a morning brief, not an email tool.
SHOW_CLIENT_EMAIL_DRAFT = False

app = FastAPI(title="Wealth Morning Brief")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _page_date() -> str:
    """Today's date in the header, e.g. '22 Jul 2026'."""
    return datetime.now(SGT).strftime("%d %b %Y")


def _paragraphs(text: str) -> list[str]:
    """Split the AI brief body on blank lines so the template can render <p> tags."""
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if parts:
        return parts
    return [text.strip()] if text.strip() else []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the main page — everything the RM sees on first load.

    Fetches once per page load:
      - market snapshot (yfinance prices)
      - top headlines (Finnhub, or static fallback if API is down)
      - sentiment score (derived from VIX + S&P momentum)

    Passes data to index.html in two forms:
      - display objects (snapshot, headlines) — what the RM reads in the UI
      - JSON strings (snapshot_json, headlines_json) — hidden in the page so
        Generate can re-post the same data without calling Finnhub/yfinance again
    """
    snapshot = fetch_market_snapshot()
    news = fetch_headlines()
    headlines = news["headlines"]
    sentiment = compute_sentiment()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "page_date": _page_date(),
            "snapshot": snapshot,
            "headlines": headlines,
            "headlines_source": news["source"],  # "finnhub" or "fallback" — shown in UI
            # Serialized copies for the hidden #brief-payload form (see index.html).
            "snapshot_json": json.dumps(snapshot),
            "headlines_json": json.dumps(headlines),
            "sentiment": sentiment,
        },
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    snapshot_json: str = Form(...),
    headlines_json: str = Form(...),
    tier: str | None = Form(None),
    goal: str | None = Form(None),
    geography: str | None = Form(None),
    asset_classes: list[str] | None = Form(None),
    portfolio_mix: str | None = Form(None),
) -> HTMLResponse:
    """Generate the AI brief and return an HTML fragment for the brief panel.

    Triggered by HTMX (auto on page load, or when RM clicks Generate on the profile form).
    Does NOT re-fetch market data — uses snapshot_json + headlines_json from the hidden form.

    Form fields:
      snapshot_json / headlines_json — hidden; baked in at page load (see GET / above)
      tier, goal, geography, asset_classes, portfolio_mix — optional client profile
    """
    # Turn the hidden JSON strings back into Python objects.
    # headlines_json is a form field NAME, not a file — see module docstring.
    try:
        snapshot: dict[str, Any] = json.loads(snapshot_json)
        headlines: list[str] = json.loads(headlines_json)
    except json.JSONDecodeError:
        logger.warning("Invalid snapshot/headlines JSON on /generate")
        snapshot = {"as_of": "", "series": []}
        headlines = []

    # Build optional client profile dict for personalised tone (llm/brief.py V2 prompt).
    profile = None
    if tier and goal and geography:
        assets = asset_classes or []
        if len(assets) > 2:
            assets = assets[:2]  # UI allows max 2 asset-class checkboxes
        profile = {
            "tier": tier,
            "goal": goal,
            "geography": geography,
            "asset_classes": assets,
        }
        mix = (portfolio_mix or "").strip()
        if mix:
            profile["portfolio_mix"] = mix

    # Hand off to the LLM layer — snapshot + headlines are function arguments, not imports.
    result = generate_brief(snapshot, headlines, profile=profile)

    # Return a partial HTML page (brief panel only) — HTMX swaps it into #brief-region.
    return templates.TemplateResponse(
        request,
        "partials/brief.html",
        {
            "ok": result["ok"],
            "paragraphs": _paragraphs(result["text"]),
            "badge": result.get("badge"),
            "ideas": result.get("ideas") or [],
            "watch": result.get("watch") or [],
            "house_view": result.get("house_view") or [],
            "email_draft": result.get("email_draft") or "",
            "show_email_draft": SHOW_CLIENT_EMAIL_DRAFT,
        },
    )


@app.get("/market")
async def market() -> dict[str, Any]:
    """JSON-only market snapshot — useful for debugging or future API consumers."""
    return fetch_market_snapshot()


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check for Railway / monitoring — returns 200 if the process is running."""
    return {"status": "ok"}
