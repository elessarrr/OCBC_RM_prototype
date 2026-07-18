"""API / page route tests (external I/O mocked)."""

from __future__ import annotations

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from llm.brief import BRIEF_UNAVAILABLE_USER_MESSAGE
from main import app

client = TestClient(app)

FAKE_SNAPSHOT = {
    "as_of": "13 Jul 2026, 10:00 SGT",
    "series": [
        {
            "symbol": "^STI",
            "label": "STI",
            "price": 5210.0,
            "change_points": 6.0,
            "change_pct": 0.12,
            "arrow": "↑",
        },
        {
            "symbol": "^GSPC",
            "label": "S&P 500",
            "price": 7472.0,
            "change_points": -28.0,
            "change_pct": -0.37,
            "arrow": "↓",
        },
    ],
}

FAKE_NEWS = {
    "source": "finnhub",
    "headlines": [
        {
            "title": "Markets rise on tech rally",
            "url": "https://example.com/1",
        },
        {
            "title": "Fed holds rates steady",
            "url": "https://example.com/2",
        },
        {
            "title": "USD softens versus Asian FX",
            "url": "https://example.com/3",
        },
    ],
}


@patch("main.fetch_headlines", return_value=FAKE_NEWS)
@patch("main.fetch_market_snapshot", return_value=FAKE_SNAPSHOT)
def test_index_renders_snapshot_without_waiting_on_llm(
    _mock_snap, _mock_news
) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Wealth Morning Brief" in response.text
    assert "Market Snapshot" in response.text
    assert "STI" in response.text
    assert "5210" in response.text
    assert "as of" in response.text
    assert "Markets rise on tech rally" in response.text
    assert "https://example.com/1" in response.text
    assert "(source)" in response.text
    assert "Finnhub" in response.text
    assert 'hx-post="/generate"' in response.text
    assert "Generating your brief" in response.text


@patch("main.fetch_headlines", return_value=FAKE_NEWS)
@patch("main.fetch_market_snapshot", return_value=FAKE_SNAPSHOT)
def test_index_includes_client_profile_form(_mock_snap, _mock_news) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Client Profile" in response.text
    assert 'name="tier"' in response.text
    assert 'name="goal"' in response.text
    assert 'name="geography"' in response.text
    assert 'name="asset_classes"' in response.text
    assert "Generate My Brief" in response.text
    assert "Mass Affluent" in response.text
    assert "Capital Preservation" in response.text


@patch("main.generate_brief")
def test_generate_uses_posted_snapshot_not_live_fetch(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Equities were mixed. Watch USD/SGD into the close.",
        "badge": None,
    }
    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
        },
    )
    assert response.status_code == 200
    assert "Equities were mixed" in response.text
    mock_gen.assert_called_once()
    args, kwargs = mock_gen.call_args
    assert args[0] == FAKE_SNAPSHOT
    assert args[1] == FAKE_NEWS["headlines"]
    assert kwargs.get("profile") is None


@patch("main.fetch_market_snapshot")
@patch("main.generate_brief")
def test_generate_with_profile_reuses_snapshot_not_yfinance(
    mock_gen, mock_snap
) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Preserve capital while USD/SGD stays choppy.",
        "badge": "Capital Preservation | HNW | Singapore Focus",
    }
    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
            "tier": "High Net Worth",
            "goal": "Capital Preservation",
            "geography": "Singapore-centric",
            "asset_classes": ["Fixed Income / Bonds", "Cash / FX"],
        },
    )
    assert response.status_code == 200
    assert "Preserve capital" in response.text
    assert "Capital Preservation | HNW | Singapore Focus" in response.text
    mock_snap.assert_not_called()
    mock_gen.assert_called_once()
    _args, kwargs = mock_gen.call_args
    assert kwargs["profile"] == {
        "tier": "High Net Worth",
        "goal": "Capital Preservation",
        "geography": "Singapore-centric",
        "asset_classes": ["Fixed Income / Bonds", "Cash / FX"],
    }


@patch("main.generate_brief")
def test_generate_caps_asset_classes_at_two(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Brief text.",
        "badge": "Aggressive Growth | Mass Affluent | Global",
    }
    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
            "tier": "Mass Affluent",
            "goal": "Aggressive Growth",
            "geography": "Global",
            "asset_classes": [
                "Global Equities",
                "Commodities",
                "Cash / FX",
            ],
        },
    )
    assert response.status_code == 200
    _args, kwargs = mock_gen.call_args
    assert kwargs["profile"]["asset_classes"] == [
        "Global Equities",
        "Commodities",
    ]


@patch("main.generate_brief")
def test_generate_shows_safe_message_on_failure(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": False,
        "text": BRIEF_UNAVAILABLE_USER_MESSAGE,
        "badge": None,
    }
    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
        },
    )
    assert response.status_code == 200
    assert BRIEF_UNAVAILABLE_USER_MESSAGE in response.text


@patch("main.fetch_market_snapshot", return_value=FAKE_SNAPSHOT)
def test_market_endpoint(_mock_snap) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of"] == FAKE_SNAPSHOT["as_of"]
    assert len(payload["series"]) == 2


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
