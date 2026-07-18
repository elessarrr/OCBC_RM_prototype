"""Tests for DeepSeek brief prompt construction and graceful failures."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm.brief import (
    BRIEF_UNAVAILABLE_USER_MESSAGE,
    MODEL,
    build_persona_badge,
    build_system_prompt,
    build_user_prompt,
    generate_brief,
)


SAMPLE_SNAPSHOT = {
    "as_of": "13 Jul 2026, 10:00 SGT",
    "series": [
        {
            "label": "STI",
            "price": 5210.0,
            "change_pct": 0.12,
            "arrow": "↑",
        },
        {
            "label": "S&P 500",
            "price": 7472.0,
            "change_pct": -0.37,
            "arrow": "↓",
        },
    ],
}

SAMPLE_HEADLINES = [
    "Markets rise on tech rally",
    "Fed holds rates steady",
    "USD softens versus Asian FX",
]


def test_build_user_prompt_includes_figures_and_headlines() -> None:
    text = build_user_prompt(SAMPLE_SNAPSHOT, SAMPLE_HEADLINES)
    assert "STI: 5210" in text or "STI: 5210.0" in text
    assert "0.12" in text
    assert "Markets rise on tech rally" in text
    assert "Write a morning market brief" in text


def test_build_system_prompt_v1_forbids_fabrication() -> None:
    prompt = build_system_prompt(profile=None)
    assert "Never fabricate" in prompt or "never fabricate" in prompt.lower()
    assert "2 paragraphs" in prompt or "two paragraphs" in prompt.lower()


def test_build_system_prompt_v2_appends_persona() -> None:
    profile = {
        "tier": "High Net Worth",
        "goal": "Capital Preservation",
        "asset_classes": ["Fixed Income / Bonds"],
        "geography": "Singapore-centric",
    }
    prompt = build_system_prompt(profile=profile)
    assert "High Net Worth" in prompt
    assert "Capital Preservation" in prompt
    assert "Fixed Income / Bonds" in prompt
    assert "Singapore-centric" in prompt
    assert "downside risk" in prompt.lower() or "defensive" in prompt.lower()
    assert "product-aware" in prompt.lower() or "balanced" in prompt.lower()
    assert "Never fabricate" in prompt or "never fabricate" in prompt.lower()


def test_build_persona_badge() -> None:
    badge = build_persona_badge(
        {
            "tier": "High Net Worth",
            "goal": "Capital Preservation",
            "geography": "Singapore-centric",
        }
    )
    assert "Capital Preservation" in badge
    assert "HNW" in badge or "High Net Worth" in badge
    assert "Singapore" in badge


@patch("llm.brief.OpenAI")
def test_generate_brief_returns_plain_text(mock_openai_cls: MagicMock) -> None:
    client = MagicMock()
    mock_openai_cls.return_value = client
    client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="Markets were mixed today. Risk sits with USD/SGD."
                )
            )
        ]
    )

    result = generate_brief(
        SAMPLE_SNAPSHOT,
        SAMPLE_HEADLINES,
        profile=None,
        api_key="test-key",
    )
    assert result["ok"] is True
    assert "Markets were mixed" in result["text"]
    assert "**" not in result["text"]
    mock_openai_cls.assert_called_once()
    assert mock_openai_cls.call_args.kwargs["base_url"] == "https://api.deepseek.com"
    client.chat.completions.create.assert_called_once()
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == MODEL
    assert kwargs["model"] == "deepseek-chat"
    assert kwargs["temperature"] == 0.4
    assert kwargs.get("max_tokens") is None or kwargs["max_tokens"] >= 1024
    messages = kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


@patch("llm.brief.OpenAI")
def test_generate_brief_graceful_on_api_error(mock_openai_cls: MagicMock) -> None:
    client = MagicMock()
    mock_openai_cls.return_value = client
    client.chat.completions.create.side_effect = Exception("boom 401 secret-key-xyz")

    result = generate_brief(
        SAMPLE_SNAPSHOT,
        SAMPLE_HEADLINES,
        profile=None,
        api_key="test-key",
    )
    assert result["ok"] is False
    assert result["text"] == BRIEF_UNAVAILABLE_USER_MESSAGE
    assert "401" not in result["text"]
    assert "secret-key" not in result["text"]


def test_generate_brief_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    result = generate_brief(
        SAMPLE_SNAPSHOT,
        SAMPLE_HEADLINES,
        profile=None,
        api_key=None,
    )
    assert result["ok"] is False
    assert result["text"] == BRIEF_UNAVAILABLE_USER_MESSAGE
