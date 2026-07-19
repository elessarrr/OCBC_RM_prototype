"""Tests for market snapshot and news fetching (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data.fallback_headlines import FALLBACK_HEADLINES
from data.market import (
    FINANCIAL_KEYWORDS,
    HEADLINE_LIMIT,
    SYMBOLS,
    _is_financial_headline,
    _sentiment_label,
    arrow_for_change,
    compute_sentiment,
    fetch_headlines,
    fetch_market_snapshot,
)


def test_arrow_for_change() -> None:
    assert arrow_for_change(0.1) == "↑"
    assert arrow_for_change(-0.1) == "↓"
    assert arrow_for_change(0.0) == "→"
    assert arrow_for_change(None) == "→"


def test_symbols_cover_eight_series() -> None:
    assert len(SYMBOLS) == 8
    labels = {s["label"] for s in SYMBOLS}
    assert labels == {
        "STI",
        "S&P 500",
        "Hang Seng",
        "Nikkei",
        "USD/SGD",
        "Gold (USD/oz)",
        "Brent Crude",
        "US 10Y Yield",
    }


def test_us10y_symbol_has_percent_suffix() -> None:
    tnx = next(s for s in SYMBOLS if s["label"] == "US 10Y Yield")
    assert tnx.get("suffix") == "%"


# --- Sentiment label ---


def test_sentiment_label_boundaries() -> None:
    assert _sentiment_label(0) == "Extreme Fear"
    assert _sentiment_label(20) == "Extreme Fear"
    assert _sentiment_label(21) == "Fear"
    assert _sentiment_label(40) == "Fear"
    assert _sentiment_label(41) == "Neutral"
    assert _sentiment_label(60) == "Neutral"
    assert _sentiment_label(61) == "Greed"
    assert _sentiment_label(80) == "Greed"
    assert _sentiment_label(81) == "Extreme Greed"
    assert _sentiment_label(100) == "Extreme Greed"


# --- compute_sentiment ---


def _fake_vix_history(vix_close: float) -> pd.DataFrame:
    return pd.DataFrame({"Close": [vix_close]}, index=pd.to_datetime(["2026-07-18"]))


def _fake_spx_history(closes: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2026-06-20", periods=len(closes), freq="B")
    return pd.DataFrame({"Close": closes}, index=dates)


@patch("data.market.yf.Ticker")
def test_compute_sentiment_returns_score_in_range(mock_ticker_cls: MagicMock) -> None:
    spx_closes = [100.0 + i * 0.5 for i in range(15)]

    def side_effect(symbol: str) -> MagicMock:
        inst = MagicMock()
        if symbol == "^VIX":
            inst.history.return_value = _fake_vix_history(15.0)
        else:
            inst.history.return_value = _fake_spx_history(spx_closes)
        return inst

    mock_ticker_cls.side_effect = side_effect

    result = compute_sentiment()
    assert result["score"] is not None
    assert 0 <= result["score"] <= 100
    assert result["label"] in {"Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"}
    assert result["vix"] == 15.0


@patch("data.market.yf.Ticker")
def test_compute_sentiment_falls_back_on_yfinance_error(mock_ticker_cls: MagicMock) -> None:
    mock_ticker_cls.side_effect = RuntimeError("yfinance down")

    result = compute_sentiment()
    assert result["score"] is None
    assert result["label"] == "Unavailable"
    assert result["vix"] is None


@patch("data.market.yf.Ticker")
def test_compute_sentiment_high_vix_scores_low(mock_ticker_cls: MagicMock) -> None:
    """VIX=50 (extreme fear) should produce a low score (≤30)."""
    spx_closes = [100.0] * 15

    def side_effect(symbol: str) -> MagicMock:
        inst = MagicMock()
        if symbol == "^VIX":
            inst.history.return_value = _fake_vix_history(50.0)
        else:
            inst.history.return_value = _fake_spx_history(spx_closes)
        return inst

    mock_ticker_cls.side_effect = side_effect
    result = compute_sentiment()
    assert result["score"] is not None
    assert result["score"] <= 30


def _fake_history_two_closes(prev: float, last: float) -> pd.DataFrame:
    return pd.DataFrame(
        {"Close": [prev, last]},
        index=pd.to_datetime(["2026-07-10", "2026-07-13"]),
    )


@patch("data.market.yf.Ticker")
def test_fetch_market_snapshot_shape(mock_ticker_cls: MagicMock) -> None:
    instance = MagicMock()
    instance.history.return_value = _fake_history_two_closes(100.0, 101.5)
    mock_ticker_cls.return_value = instance

    snapshot = fetch_market_snapshot()

    assert "as_of" in snapshot
    assert "SGT" in snapshot["as_of"] or "+08" in snapshot["as_of"]
    assert len(snapshot["series"]) == 8
    first = snapshot["series"][0]
    assert first["label"] == "STI"
    assert first["price"] == pytest.approx(101.5)
    assert first["change_pct"] == pytest.approx(1.5)
    assert first["arrow"] == "↑"
    assert "change_points" in first


@patch("data.market.yf.Ticker")
def test_fetch_market_snapshot_last_close_when_flat(mock_ticker_cls: MagicMock) -> None:
    instance = MagicMock()
    instance.history.return_value = _fake_history_two_closes(200.0, 200.0)
    mock_ticker_cls.return_value = instance

    snapshot = fetch_market_snapshot()
    assert snapshot["series"][0]["arrow"] == "→"
    assert snapshot["series"][0]["price"] == 200.0


@patch("data.market.httpx.get")
def test_fetch_headlines_happy_path_includes_urls_and_cap(mock_get: MagicMock) -> None:
    general = [
        {"headline": f"Fed signals rate {i}", "url": f"https://example.com/g{i}"}
        for i in range(1, 8)
    ]
    forex = [
        {"headline": f"USD/SGD forex move {i}", "url": f"https://example.com/f{i}"}
        for i in range(1, 6)
    ]
    mock_get.side_effect = [
        MagicMock(
            status_code=200,
            json=lambda: general,
            raise_for_status=lambda: None,
        ),
        MagicMock(
            status_code=200,
            json=lambda: forex,
            raise_for_status=lambda: None,
        ),
    ]

    result = fetch_headlines(api_key="test-key")
    assert result["source"] == "finnhub"
    assert len(result["headlines"]) == HEADLINE_LIMIT
    assert HEADLINE_LIMIT == 10
    first = result["headlines"][0]
    assert "Fed" in first["title"] or "USD" in first["title"]
    assert first["url"].startswith("https://example.com/")
    assert all(h.get("url") for h in result["headlines"])


def test_is_financial_headline_accepts_market_terms() -> None:
    assert _is_financial_headline("Fed signals rate cut next quarter")
    assert _is_financial_headline("S&P 500 hits record high on earnings beat")
    assert _is_financial_headline("USD/SGD steady ahead of inflation print")
    assert _is_financial_headline("Brent crude slides as OPEC signals output hike")
    assert _is_financial_headline("Singapore GDP growth beats forecast")


def test_is_financial_headline_rejects_non_financial_news() -> None:
    assert not _is_financial_headline("UFC champion defends title at MSG")
    assert not _is_financial_headline("Premier League results: Arsenal 2-1 City")
    assert not _is_financial_headline("Celebrity couple announces wedding date")


@patch("data.market.httpx.get")
def test_fetch_headlines_filters_general_keeps_forex(mock_get: MagicMock) -> None:
    """Non-financial general headlines are dropped; all forex headlines pass through."""
    general = [
        {"headline": "UFC fighter signs new deal", "url": "https://example.com/ufc"},
        {"headline": "Markets rally on Fed rate outlook", "url": "https://example.com/fed"},
        {"headline": "Celebrity news dominates weekend", "url": "https://example.com/cel"},
        {"headline": "Oil prices rise on OPEC cut", "url": "https://example.com/oil"},
    ]
    forex = [
        {"headline": "EUR/USD ticks higher on ECB minutes", "url": "https://example.com/eur"},
    ]
    mock_get.side_effect = [
        MagicMock(status_code=200, json=lambda: general, raise_for_status=lambda: None),
        MagicMock(status_code=200, json=lambda: forex, raise_for_status=lambda: None),
    ]

    result = fetch_headlines(api_key="test-key")
    titles = [h["title"] for h in result["headlines"]]

    assert "UFC fighter signs new deal" not in titles
    assert "Celebrity news dominates weekend" not in titles
    assert "Markets rally on Fed rate outlook" in titles
    assert "Oil prices rise on OPEC cut" in titles
    assert "EUR/USD ticks higher on ECB minutes" in titles


@patch("data.market.httpx.get")
def test_fetch_headlines_includes_unfiltered_overflow_to_reach_minimum(
    mock_get: MagicMock,
) -> None:
    """If filtered pool < 3, pull in enough unfiltered general headlines to avoid fallback."""
    general = [
        {"headline": "UFC event preview", "url": "https://example.com/ufc"},
        {"headline": "Dana White confirms card", "url": "https://example.com/dana"},
        {"headline": "Sports roundup Saturday", "url": "https://example.com/sport"},
    ]
    forex = [
        {"headline": "USD/SGD steady ahead of CPI", "url": "https://example.com/sgd"},
        {"headline": "EUR/USD holds range", "url": "https://example.com/eur"},
    ]
    mock_get.side_effect = [
        MagicMock(status_code=200, json=lambda: general, raise_for_status=lambda: None),
        MagicMock(status_code=200, json=lambda: forex, raise_for_status=lambda: None),
    ]

    result = fetch_headlines(api_key="test-key")
    assert result["source"] == "finnhub"
    assert len(result["headlines"]) >= 3


@patch("data.market.httpx.get")
def test_fetch_headlines_falls_back_on_error(mock_get: MagicMock) -> None:
    mock_get.side_effect = Exception("timeout")

    result = fetch_headlines(api_key="test-key")
    assert result["source"] == "fallback"
    assert result["headlines"] == FALLBACK_HEADLINES
    assert len(result["headlines"]) >= 3
    assert all(isinstance(h, dict) and h.get("title") for h in result["headlines"])


def test_fallback_headlines_are_curated() -> None:
    assert len(FALLBACK_HEADLINES) >= 3
    assert all(
        isinstance(h, dict) and h.get("title", "").strip() for h in FALLBACK_HEADLINES
    )
