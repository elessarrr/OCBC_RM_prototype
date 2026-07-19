"""Tests for DeepSeek brief prompt construction and graceful failures."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm.brief import (
    BRIEF_UNAVAILABLE_USER_MESSAGE,
    MODEL,
    build_client_email,
    build_persona_badge,
    build_system_prompt,
    build_user_prompt,
    generate_brief,
    parse_structured_brief_response,
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


def test_parse_structured_brief_response_extracts_all_blocks() -> None:
    parsed = parse_structured_brief_response(
        """BRIEF:
Markets were mixed overnight.

Singapore assets stayed resilient.

INVESTMENT_IDEAS:
1. Review high-quality short-duration bonds.
2. Keep selective exposure to dividend equities.

WATCH:
1. USD/SGD reaction to regional data
2. US 10-year yield direction
3. Equity volatility into the close

HOUSE_VIEW:
1. Stay balanced across risk assets.
2. Prefer quality income over chasing momentum."""
    )

    assert parsed["paragraphs"] == [
        "Markets were mixed overnight.",
        "Singapore assets stayed resilient.",
    ]
    assert parsed["ideas"] == [
        "Review high-quality short-duration bonds.",
        "Keep selective exposure to dividend equities.",
    ]
    assert parsed["watch"] == [
        "USD/SGD reaction to regional data",
        "US 10-year yield direction",
        "Equity volatility into the close",
    ]
    assert parsed["house_view"] == [
        "Stay balanced across risk assets.",
        "Prefer quality income over chasing momentum.",
    ]


def test_parse_structured_brief_response_soft_fails_missing_blocks() -> None:
    parsed = parse_structured_brief_response(
        "BRIEF:\nMarkets were mixed. Focus on portfolio resilience."
    )

    assert parsed["paragraphs"] == [
        "Markets were mixed. Focus on portfolio resilience."
    ]
    assert parsed["ideas"] == []
    assert parsed["watch"] == []
    assert parsed["house_view"] == []


def test_build_client_email_wraps_brief_in_canonical_template() -> None:
    brief = "Markets were mixed overnight.\n\nStay selective into the close."

    assert build_client_email(brief) == """Dear [CLIENT_NAME],

Hope you're doing well. We wanted to share our perspective on the markets today, and what it means for your portfolio.

Markets were mixed overnight.

Stay selective into the close.

We'd be happy to discuss any next steps.

Thanks,
[RM_NAME]"""


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
                    content="""BRIEF:
Markets were mixed today. Risk sits with USD/SGD.

INVESTMENT_IDEAS:
1. Review short-duration bonds.
2. Keep selective equity exposure.

WATCH:
1. USD/SGD direction
2. US Treasury yields
3. Regional equity volatility

HOUSE_VIEW:
1. Maintain balanced positioning.
2. Prefer quality income."""
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
    assert result["ideas"] == [
        "Review short-duration bonds.",
        "Keep selective equity exposure.",
    ]
    assert result["watch"] == [
        "USD/SGD direction",
        "US Treasury yields",
        "Regional equity volatility",
    ]
    assert result["house_view"] == [
        "Maintain balanced positioning.",
        "Prefer quality income.",
    ]
    assert result["email_draft"].startswith("Dear [CLIENT_NAME],")
    assert "Markets were mixed today." in result["email_draft"]
    assert result["email_draft"].endswith("[RM_NAME]")
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
    assert result["ideas"] == []
    assert result["watch"] == []
    assert result["house_view"] == []
    assert result["email_draft"] == ""
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
    assert result["ideas"] == []
    assert result["watch"] == []
    assert result["house_view"] == []
    assert result["email_draft"] == ""
