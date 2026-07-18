"""Tests for market snapshot and news fetching (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data.fallback_headlines import FALLBACK_HEADLINES
from data.market import (
    HEADLINE_LIMIT,
    SYMBOLS,
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
        {"headline": f"General story {i}", "url": f"https://example.com/g{i}"}
        for i in range(1, 8)
    ]
    forex = [
        {"headline": f"Forex story {i}", "url": f"https://example.com/f{i}"}
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
    assert first["title"] == "General story 1"
    assert first["url"] == "https://example.com/g1"
    assert all(h.get("url") for h in result["headlines"])


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
