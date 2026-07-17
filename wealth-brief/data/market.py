"""Market snapshot (yfinance) and headlines (Finnhub + fallback)."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import yfinance as yf

from data.fallback_headlines import FALLBACK_HEADLINES

logger = logging.getLogger(__name__)

SGT = ZoneInfo("Asia/Singapore")
HEADLINE_LIMIT = 10
FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"

SYMBOLS: list[dict[str, str]] = [
    {"symbol": "^STI", "label": "STI"},
    {"symbol": "^GSPC", "label": "S&P 500"},
    {"symbol": "^HSI", "label": "Hang Seng"},
    {"symbol": "^N225", "label": "Nikkei"},
    {"symbol": "USDSGD=X", "label": "USD/SGD"},
    {"symbol": "GC=F", "label": "Gold (USD/oz)"},
    {"symbol": "BZ=F", "label": "Brent Crude"},
]


def arrow_for_change(change_pct: float | None) -> str:
    if change_pct is None or change_pct == 0:
        return "→"
    if change_pct > 0:
        return "↑"
    return "↓"


def _format_as_of(when: datetime | None = None) -> str:
    now = when or datetime.now(SGT)
    return now.strftime("%d %b %Y, %H:%M SGT")


def _series_from_history(label: str, symbol: str, hist: Any) -> dict[str, Any]:
    """Build one series dict from a yfinance history DataFrame (last close OK)."""
    if hist is None or getattr(hist, "empty", True) or "Close" not in hist.columns:
        return {
            "symbol": symbol,
            "label": label,
            "price": None,
            "change_points": None,
            "change_pct": None,
            "arrow": "→",
        }

    closes = hist["Close"].dropna()
    if closes.empty:
        return {
            "symbol": symbol,
            "label": label,
            "price": None,
            "change_points": None,
            "change_pct": None,
            "arrow": "→",
        }

    last = float(closes.iloc[-1])
    if len(closes) >= 2:
        prev = float(closes.iloc[-2])
    else:
        prev = last

    change_points = last - prev
    change_pct = (change_points / prev * 100.0) if prev else 0.0

    return {
        "symbol": symbol,
        "label": label,
        "price": round(last, 4 if "USD" in label or label in {"Gold (USD/oz)", "Brent Crude"} else 2),
        "change_points": round(change_points, 4),
        "change_pct": round(change_pct, 2),
        "arrow": arrow_for_change(change_pct),
    }


def fetch_market_snapshot() -> dict[str, Any]:
    """Fetch all configured series. Uses recent history so closed markets show last close."""
    series: list[dict[str, Any]] = []
    for item in SYMBOLS:
        symbol = item["symbol"]
        label = item["label"]
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            series.append(_series_from_history(label, symbol, hist))
        except Exception:
            logger.exception("Failed to fetch %s (%s)", label, symbol)
            series.append(
                {
                    "symbol": symbol,
                    "label": label,
                    "price": None,
                    "change_points": None,
                    "change_pct": None,
                    "arrow": "→",
                }
            )

    return {"as_of": _format_as_of(), "series": series}


def _finnhub_category(api_key: str, category: str, timeout: float = 8.0) -> list[dict[str, str]]:
    response = httpx.get(
        FINNHUB_NEWS_URL,
        params={"category": category, "token": api_key},
        timeout=timeout,
        trust_env=False,
    )
    response.raise_for_status()
    payload = response.json()
    headlines: list[dict[str, str]] = []
    if isinstance(payload, list):
        for row in payload:
            if not isinstance(row, dict):
                continue
            text = (row.get("headline") or "").strip()
            url = (row.get("url") or "").strip()
            if text and url:
                headlines.append({"title": text, "url": url})
    return headlines


def fetch_headlines(api_key: str | None = None) -> dict[str, Any]:
    """Fetch general + forex headlines; fall back to static list on any failure."""
    key = api_key if api_key is not None else os.environ.get("FINNHUB_API_KEY")
    if not key:
        logger.warning("FINNHUB_API_KEY missing; using fallback headlines")
        return {"source": "fallback", "headlines": list(FALLBACK_HEADLINES)}

    try:
        general = _finnhub_category(key, "general")
        forex = _finnhub_category(key, "forex")
        combined: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in general + forex:
            title = item["title"]
            if title not in seen:
                seen.add(title)
                combined.append(item)
            if len(combined) >= HEADLINE_LIMIT:
                break
        if len(combined) < 3:
            raise ValueError("Fewer than 3 headlines from Finnhub")
        return {"source": "finnhub", "headlines": combined}
    except Exception as exc:
        logger.warning("Finnhub unavailable (%s); using fallback headlines", exc)
        return {"source": "fallback", "headlines": list(FALLBACK_HEADLINES)}
