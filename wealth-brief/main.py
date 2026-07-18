"""Wealth Morning Brief — FastAPI entrypoint."""

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

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SGT = ZoneInfo("Asia/Singapore")

app = FastAPI(title="Wealth Morning Brief")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _page_date() -> str:
    return datetime.now(SGT).strftime("%d %b %Y")


def _paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if parts:
        return parts
    return [text.strip()] if text.strip() else []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
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
            "headlines_source": news["source"],
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
) -> HTMLResponse:
    """Generate brief from the in-page snapshot — does not re-fetch yfinance."""
    try:
        snapshot: dict[str, Any] = json.loads(snapshot_json)
        headlines: list[str] = json.loads(headlines_json)
    except json.JSONDecodeError:
        logger.warning("Invalid snapshot/headlines JSON on /generate")
        snapshot = {"as_of": "", "series": []}
        headlines = []

    profile = None
    if tier and goal and geography:
        assets = asset_classes or []
        if len(assets) > 2:
            assets = assets[:2]
        profile = {
            "tier": tier,
            "goal": goal,
            "geography": geography,
            "asset_classes": assets,
        }

    result = generate_brief(snapshot, headlines, profile=profile)
    return templates.TemplateResponse(
        request,
        "partials/brief.html",
        {
            "ok": result["ok"],
            "paragraphs": _paragraphs(result["text"]),
            "badge": result.get("badge"),
        },
    )


@app.get("/market")
async def market() -> dict[str, Any]:
    return fetch_market_snapshot()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
