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
        "Markets rise on tech rally",
        "Fed holds rates steady",
        "USD softens versus Asian FX",
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
    assert 'hx-post="/generate"' in response.text
    assert "Generating your brief" in response.text


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
