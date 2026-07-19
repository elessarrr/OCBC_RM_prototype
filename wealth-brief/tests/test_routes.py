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

FAKE_SENTIMENT = {"score": 62, "label": "Greed", "vix": 14.2, "sp10d_pct": 1.8}


@patch("main.compute_sentiment", return_value=FAKE_SENTIMENT)
@patch("main.fetch_headlines", return_value=FAKE_NEWS)
@patch("main.fetch_market_snapshot", return_value=FAKE_SNAPSHOT)
def test_index_renders_snapshot_without_waiting_on_llm(
    _mock_snap, _mock_news, _mock_sentiment
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


@patch("main.compute_sentiment", return_value=FAKE_SENTIMENT)
@patch("main.fetch_headlines", return_value=FAKE_NEWS)
@patch("main.fetch_market_snapshot", return_value=FAKE_SNAPSHOT)
def test_index_includes_client_profile_form(_mock_snap, _mock_news, _mock_sentiment) -> None:
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


@patch("main.compute_sentiment", return_value=FAKE_SENTIMENT)
@patch("main.fetch_headlines", return_value=FAKE_NEWS)
@patch("main.fetch_market_snapshot", return_value=FAKE_SNAPSHOT)
def test_index_includes_prototype_disclaimer(
    _mock_snap, _mock_news, _mock_sentiment
) -> None:
    response = client.get("/")
    text = " ".join(response.text.split())

    assert response.status_code == 200
    assert "Demonstration prototype" in text
    assert "AI-generated for demonstration" in text
    assert "not official OCBC research, advice, or a bank recommendation" in text
    assert "approved proprietary research" in text


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
def test_generate_renders_demo_investment_ideas(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Markets were mixed. Maintain selective exposure.",
        "badge": "Capital Preservation | HNW | Singapore Focus",
        "ideas": [
            "Review high-quality short-duration bonds.",
            "Keep selective exposure to dividend equities.",
        ],
        "watch": [],
        "house_view": [],
    }

    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
            "tier": "High Net Worth",
            "goal": "Capital Preservation",
            "geography": "Singapore-centric",
        },
    )

    assert response.status_code == 200
    assert "Investment ideas (demo)" in response.text
    assert "Review high-quality short-duration bonds." in response.text
    assert "Keep selective exposure to dividend equities." in response.text


@patch("main.generate_brief")
def test_generate_hides_disabled_client_email_draft(mock_gen) -> None:
    """Email draft stays in code but is UI-disabled for a client-facing brief."""
    mock_gen.return_value = {
        "ok": True,
        "text": "Markets were mixed. Maintain selective exposure.",
        "badge": None,
        "ideas": [],
        "watch": [],
        "house_view": [],
        "email_draft": (
            "Dear [CLIENT_NAME],\n\nMarkets were mixed.\n\nThanks,\n[RM_NAME]"
        ),
    }

    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
        },
    )

    assert response.status_code == 200
    assert "Markets were mixed. Maintain selective exposure." in response.text
    assert "Draft email to client" not in response.text
    assert "Dear [CLIENT_NAME]" not in response.text
    assert "Copy email" not in response.text


@patch("main.generate_brief")
def test_generate_renders_three_what_to_watch_items(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Markets were mixed.",
        "badge": None,
        "ideas": [],
        "watch": ["USD/SGD direction", "US Treasury yields", "Regional volatility"],
        "house_view": [],
        "email_draft": "",
    }

    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
        },
    )

    assert response.status_code == 200
    assert "What to watch today" in response.text
    assert "USD/SGD direction" in response.text
    assert "US Treasury yields" in response.text
    assert "Regional volatility" in response.text


@patch("main.generate_brief")
def test_generate_hides_incomplete_what_to_watch_without_failing_brief(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "The grounded brief still renders.",
        "badge": None,
        "ideas": [],
        "watch": ["Only one item"],
        "house_view": [],
        "email_draft": "",
    }

    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
        },
    )

    assert response.status_code == 200
    assert "The grounded brief still renders." in response.text
    assert "What to watch today" not in response.text
    assert "Simulated research view" not in response.text


@patch("main.generate_brief")
def test_generate_renders_simulated_research_view(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Markets were mixed.",
        "badge": None,
        "ideas": [],
        "watch": [],
        "house_view": [
            "Maintain balanced positioning.",
            "Prefer quality income over momentum.",
        ],
        "email_draft": "",
    }

    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
        },
    )

    assert response.status_code == 200
    assert "Simulated research view (demo)" in response.text
    assert "not official OCBC research" in response.text
    assert "Maintain balanced positioning." in response.text
    assert "Prefer quality income over momentum." in response.text


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
            "portfolio_mix": "40% equities / 50% bonds / 10% cash",
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
        "portfolio_mix": "40% equities / 50% bonds / 10% cash",
    }


@patch("main.generate_brief")
def test_generate_omits_blank_portfolio_mix_from_profile(mock_gen) -> None:
    mock_gen.return_value = {
        "ok": True,
        "text": "Income assets remained in focus.",
        "badge": "Income Generation | HNW | Regional Asia",
    }

    response = client.post(
        "/generate",
        data={
            "snapshot_json": json.dumps(FAKE_SNAPSHOT),
            "headlines_json": json.dumps(FAKE_NEWS["headlines"]),
            "tier": "High Net Worth",
            "goal": "Income Generation",
            "geography": "Regional Asia",
            "portfolio_mix": "   ",
        },
    )

    assert response.status_code == 200
    profile = mock_gen.call_args.kwargs["profile"]
    assert "portfolio_mix" not in profile


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
