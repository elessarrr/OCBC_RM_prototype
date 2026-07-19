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

# Terms that indicate a headline is relevant to a wealth / morning brief.
# Forex headlines bypass this filter entirely (already on-topic by category).
FINANCIAL_KEYWORDS: frozenset[str] = frozenset([
    "rate", "rates", "fed", "federal reserve", "central bank",
    "inflation", "gdp", "yield", "yields", "bond", "bonds",
    "equity", "equities", "stock", "stocks", "market", "markets",
    "trading", "trade", "earnings", "revenue", "profit",
    "economic", "economy", "fiscal", "monetary",
    "currency", "dollar", "euro", "yen", "sgd",
    "oil", "crude", "gold", "commodity", "commodities",
    "index", "indices", "fund", "hedge",
    "investment", "investor", "investors",
    "bank", "banking", "finance", "financial",
    "debt", "deficit", "surplus", "growth", "recession",
    "credit", "risk", "volatility", "nasdaq", "dow", "s&p",
    "nikkei", "sti", "hang seng", "brent", "opec",
    "treasury", "ipo", "acquisition", "merger",
    "dividend", "buyback", "quarter", "quarterly",
    "forecast", "outlook", "tariff", "tariffs",
    "sanction", "sanctions", "export", "import",
    "pmi", "cpi", "pce", "nonfarm", "payroll", "unemployment",
    "interest", "hike", "cut", "pivot", "tightening", "easing",
    "rally", "selloff", "correction", "bull", "bear",
    "singapore", "china", "asia", "macro",
])


def _is_financial_headline(title: str) -> bool:
    """Return True if the headline contains at least one financial keyword."""
    lower = title.lower()
    return any(kw in lower for kw in FINANCIAL_KEYWORDS)

SYMBOLS: list[dict[str, str]] = [
    {"symbol": "^STI", "label": "STI"},
    {"symbol": "^GSPC", "label": "S&P 500"},
    {"symbol": "^HSI", "label": "Hang Seng"},
    {"symbol": "^N225", "label": "Nikkei"},
    {"symbol": "USDSGD=X", "label": "USD/SGD"},
    {"symbol": "GC=F", "label": "Gold (USD/oz)"},
    {"symbol": "BZ=F", "label": "Brent Crude"},
    {"symbol": "^TNX", "label": "US 10Y Yield", "suffix": "%"},
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


def _series_from_history(label: str, symbol: str, hist: Any, suffix: str = "") -> dict[str, Any]:
    """Build one series dict from a yfinance history DataFrame (last close OK)."""
    if hist is None or getattr(hist, "empty", True) or "Close" not in hist.columns:
        return {
            "symbol": symbol,
            "label": label,
            "price": None,
            "change_points": None,
            "change_pct": None,
            "arrow": "→",
            "suffix": suffix,
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
            "suffix": suffix,
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
        "suffix": suffix,
    }


def fetch_market_snapshot() -> dict[str, Any]:
    """Fetch all configured series. Uses recent history so closed markets show last close."""
    series: list[dict[str, Any]] = []
    for item in SYMBOLS:
        symbol = item["symbol"]
        label = item["label"]
        suffix = item.get("suffix", "")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            series.append(_series_from_history(label, symbol, hist, suffix=suffix))
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
                    "suffix": suffix,
                }
            )

    return {"as_of": _format_as_of(), "series": series}


def _sentiment_label(score: int) -> str:
    if score <= 20:
        return "Extreme Fear"
    if score <= 40:
        return "Fear"
    if score <= 60:
        return "Neutral"
    if score <= 80:
        return "Greed"
    return "Extreme Greed"


def compute_sentiment() -> dict[str, Any]:
    """Compute a 0–100 Fear & Greed score from VIX (60%) and S&P 500 10-day momentum (40%)."""
    try:
        vix_hist = yf.Ticker("^VIX").history(period="5d")
        vix_val = float(vix_hist["Close"].dropna().iloc[-1])

        spx_hist = yf.Ticker("^GSPC").history(period="20d")
        closes = spx_hist["Close"].dropna()
        lookback = min(10, len(closes) - 1)
        sp10d = (
            (float(closes.iloc[-1]) / float(closes.iloc[-lookback - 1]) - 1) * 100
            if lookback > 0
            else 0.0
        )

        vix_score = max(0.0, min(100.0, 100.0 - (vix_val - 10.0) / 30.0 * 100.0))
        momentum_score = max(0.0, min(100.0, 50.0 + sp10d * 5.0))
        score = round(0.6 * vix_score + 0.4 * momentum_score)

        return {
            "score": score,
            "label": _sentiment_label(score),
            "vix": round(vix_val, 1),
            "sp10d_pct": round(sp10d, 2),
        }
    except Exception:
        logger.exception("Failed to compute sentiment")
        return {"score": None, "label": "Unavailable", "vix": None, "sp10d_pct": None}


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
    """Fetch general + forex headlines; fall back to static list on any failure.

    General headlines are filtered to financial topics via FINANCIAL_KEYWORDS.
    If the filtered pool would drop below 3, unfiltered general headlines are
    appended as overflow so the demo never goes blank.
    """
    key = api_key if api_key is not None else os.environ.get("FINNHUB_API_KEY")
    if not key:
        logger.warning("FINNHUB_API_KEY missing; using fallback headlines")
        return {"source": "fallback", "headlines": list(FALLBACK_HEADLINES)}

    try:
        general = _finnhub_category(key, "general")
        forex = _finnhub_category(key, "forex")

        # Forex is already on-topic; general gets keyword-filtered.
        financial_general = [h for h in general if _is_financial_headline(h["title"])]
        other_general = [h for h in general if not _is_financial_headline(h["title"])]

        # Combine: filtered general first, then forex, then overflow if needed.
        combined: list[dict[str, str]] = []
        seen: set[str] = set()

        def _add(items: list[dict[str, str]]) -> None:
            for item in items:
                title = item["title"]
                if title not in seen:
                    seen.add(title)
                    combined.append(item)
                if len(combined) >= HEADLINE_LIMIT:
                    return

        _add(financial_general)
        _add(forex)

        # Soft overflow: pull in non-financial general headlines only if the
        # combined pool is still too thin to be useful.
        if len(combined) < 3:
            _add(other_general)

        if len(combined) < 3:
            raise ValueError("Fewer than 3 headlines from Finnhub after filtering")

        return {"source": "finnhub", "headlines": combined}
    except Exception as exc:
        logger.warning("Finnhub unavailable (%s); using fallback headlines", exc)
        return {"source": "fallback", "headlines": list(FALLBACK_HEADLINES)}
