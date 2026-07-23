"""Market snapshot (yfinance) and headlines (Finnhub + fallback).

Three jobs live here:
1. fetch_market_snapshot() — 8 live series for the dashboard tiles
2. compute_sentiment()    — lightweight 0–100 Fear & Greed heuristic
3. fetch_headlines()      — Finnhub news, keyword-filtered, with static fallback

All external calls degrade gracefully: missing prices show as None / →,
sentiment becomes "Unavailable", headlines swap to FALLBACK_HEADLINES.
"""

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

# ---------------------------------------------------------------------------
# Headline relevance filter
# ---------------------------------------------------------------------------
# Finnhub's "general" category mixes markets with sports/celebrity noise.
# We keep a headline if its title contains any of these terms.
# Forex category headlines bypass this filter (already on-topic by category).
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
    """True if the title matches at least one FINANCIAL_KEYWORDS term."""
    lower = title.lower()
    return any(kw in lower for kw in FINANCIAL_KEYWORDS)


# ---------------------------------------------------------------------------
# Market snapshot (yfinance)
# ---------------------------------------------------------------------------
# Yahoo Finance tickers shown on the home page. Order = display order.
# "suffix" is only used for US 10Y so the UI can append "%".
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
    """Map day-over-day % change to ↑ / ↓ / → for the UI tiles."""
    if change_pct is None or change_pct == 0:
        return "→"
    if change_pct > 0:
        return "↑"
    return "↓"


def _format_as_of(when: datetime | None = None) -> str:
    """Human-readable timestamp stamped on the snapshot (Singapore time)."""
    now = when or datetime.now(SGT)
    return now.strftime("%d %b %Y, %H:%M SGT")


def _series_from_history(label: str, symbol: str, hist: Any, suffix: str = "") -> dict[str, Any]:
    """Turn a yfinance history DataFrame into one UI series dict.

    Uses the last two available closes so closed markets still show last close
    vs prior session (not a blank or zeroed tile).
    """
    # Empty / missing history → null tile rather than crashing the page.
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
    # One data point only (e.g. brand-new series): treat change as flat.
    if len(closes) >= 2:
        prev = float(closes.iloc[-2])
    else:
        prev = last

    change_points = last - prev
    change_pct = (change_points / prev * 100.0) if prev else 0.0

    # FX / commodities need more decimal places than index levels.
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
    """Fetch all configured series for the dashboard.

    period="5d" is enough to get the last two trading closes even over a
    weekend. Per-symbol failures become null tiles; the rest still render.
    """
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


# ---------------------------------------------------------------------------
# Market sentiment (demo Fear & Greed heuristic)
# ---------------------------------------------------------------------------
# Not a calibrated model — a transparent, interview-explainable 0–100 score:
#   60% VIX level (higher VIX → more fear → lower score)
#   40% S&P 500 ~10-trading-day momentum
# Labels mirror CNN-style buckets for familiarity in the UI.


def _sentiment_label(score: int) -> str:
    """Map a 0–100 score onto Extreme Fear … Extreme Greed buckets."""
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
    """Compute a 0–100 Fear & Greed score from VIX (60%) and S&P 10-day momentum (40%).

    History windows differ on purpose:
    - VIX period="5d": we only need the latest close; 5d buffers weekends.
    - SPX period="20d": we need ~10 trading days of closes for the return;
      calendar 20d is enough after weekends/holidays.
    """
    try:
        # --- VIX component: latest close only ---
        vix_hist = yf.Ticker("^VIX").history(period="5d")
        vix_val = float(vix_hist["Close"].dropna().iloc[-1])

        # --- Momentum component: ~10 trading-day % return ---
        spx_hist = yf.Ticker("^GSPC").history(period="20d")
        closes = spx_hist["Close"].dropna()
        lookback = min(10, len(closes) - 1)  # shrink if history is thin
        sp10d = (
            (float(closes.iloc[-1]) / float(closes.iloc[-lookback - 1]) - 1) * 100
            if lookback > 0
            else 0.0
        )

        # --- Map raw market inputs onto a shared 0–100 "greed" scale ---
        #
        # VIX (fear index): higher = more fear, so we *invert* it onto the score.
        # Anchor points (demo heuristic, not empirically fitted):
        #   VIX ≈ 10  → calm markets  → score 100
        #   VIX ≈ 40  → panic         → score 0
        # Distance from 10, as a fraction of the 30-point span (40−10), times 100,
        # then subtract from 100 so calm is high and panic is low:
        #   vix_score = 100 − ((vix − 10) / 30) × 100
        # Examples: VIX 10 → 100; VIX 25 → 50; VIX 40 → 0.
        # max/min clamp anything outside [10, 40] into [0, 100].
        vix_score = max(0.0, min(100.0, 100.0 - (vix_val - 10.0) / 30.0 * 100.0))

        # S&P 10-day % return: 0% is "neutral" at 50; each +1% adds 5 points.
        # So +10% over ~10 sessions → 100; −10% → 0. Again clamped to [0, 100].
        # Examples: +2% → 60; −4% → 30.
        momentum_score = max(0.0, min(100.0, 50.0 + sp10d * 5.0))

        # Final score: VIX weighted more heavily (60%) because volatility is the
        # classic Fear & Greed signal; momentum is the secondary tilt (40%).
        score = round(0.6 * vix_score + 0.4 * momentum_score)

        return {
            "score": score,
            "label": _sentiment_label(score),
            "vix": round(vix_val, 1),
            "sp10d_pct": round(sp10d, 2),
        }
    except Exception:
        # yfinance / network failure → hide the widget rather than invent a score
        logger.exception("Failed to compute sentiment")
        return {"score": None, "label": "Unavailable", "vix": None, "sp10d_pct": None}


# ---------------------------------------------------------------------------
# Headlines (Finnhub + static fallback)
# ---------------------------------------------------------------------------


def _finnhub_category(api_key: str, category: str, timeout: float = 8.0) -> list[dict[str, str]]:
    """GET /news?category=… and normalise to {title, url} dicts.

    trust_env=False skips local HTTP_PROXY settings that can 403 outbound calls
    in some Cursor / corporate environments.
    """
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

    Pipeline:
    1. Pull Finnhub `general` and `forex`.
    2. Keyword-filter `general` (drop UFC / celebrity / sports noise).
    3. Prefer filtered general, then forex, up to HEADLINE_LIMIT.
    4. If the pool still has fewer than 3 items, allow unfiltered general
       as soft overflow so the demo never goes blank.
    5. On missing key, HTTP errors, or still-too-few → FALLBACK_HEADLINES.
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
            """Append unique titles until we hit HEADLINE_LIMIT."""
            for item in items:
                title = item["title"]
                if title not in seen:
                    seen.add(title)
                    combined.append(item)
                if len(combined) >= HEADLINE_LIMIT:
                    return

        _add(financial_general)
        _add(forex)

        # Soft overflow: non-financial general only if the pool is still too thin.
        if len(combined) < 3:
            _add(other_general)

        if len(combined) < 3:
            raise ValueError("Fewer than 3 headlines from Finnhub after filtering")

        return {"source": "finnhub", "headlines": combined}
    except Exception as exc:
        logger.warning("Finnhub unavailable (%s); using fallback headlines", exc)
        return {"source": "fallback", "headlines": list(FALLBACK_HEADLINES)}
