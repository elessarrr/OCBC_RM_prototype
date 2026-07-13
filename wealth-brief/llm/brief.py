"""Claude morning-brief generation with graceful degradation."""

from __future__ import annotations

import logging
import os
from typing import Any

from anthropic import Anthropic

logger = logging.getLogger(__name__)

BRIEF_UNAVAILABLE_USER_MESSAGE = (
    "Brief temporarily unavailable. Please try again."
)

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0.4

V1_SYSTEM_PROMPT = """You are a senior wealth analyst writing a morning market brief for a private banking client.
Write in clear, professional English. Be concise — 2 paragraphs, no bullet points.
Do not use filler phrases. Lead with what moved and why it matters.
Never fabricate data — only reference the figures provided.
End with one sentence framing the key risk or opportunity for the day.
Do not use markdown formatting — plain paragraphs only."""

V2_SYSTEM_PROMPT_ADDITION = """
You are writing for a specific client profile. Adapt your brief accordingly:

Wealth tier: {tier}
Primary goal: {goal}
Asset class focus: {asset_classes}
Geography focus: {geography}

Tone guidance:
- Mass Affluent: plain language, practical, one clear action signal
- High Net Worth: product-aware, balanced risk/return framing
- Ultra HNW: brief, strategic, no hand-holding

Goal guidance:
- Capital Preservation: emphasise downside risk, volatility, defensive positioning
- Income Generation: emphasise yield, dividend-paying assets, income proxies
- Aggressive Growth: emphasise momentum, sector rotation, upside catalysts
- Legacy Planning: emphasise structural themes, long-term positioning, geopolitical context

Focus your market commentary on the asset classes and geography selected.
Do not mention asset classes or geographies not selected unless directly relevant to a major move.
"""

TIER_SHORT = {
    "Mass Affluent": "Mass Affluent",
    "High Net Worth": "HNW",
    "Ultra High Net Worth": "UHNW",
}

GEO_SHORT = {
    "Singapore-centric": "Singapore Focus",
    "Regional Asia": "Regional Asia",
    "Global": "Global",
}


def build_system_prompt(profile: dict[str, Any] | None = None) -> str:
    if not profile:
        return V1_SYSTEM_PROMPT
    assets = profile.get("asset_classes") or []
    if isinstance(assets, str):
        assets_text = assets
    else:
        assets_text = ", ".join(assets)
    addition = V2_SYSTEM_PROMPT_ADDITION.format(
        tier=profile.get("tier", ""),
        goal=profile.get("goal", ""),
        asset_classes=assets_text,
        geography=profile.get("geography", ""),
    )
    return f"{V1_SYSTEM_PROMPT}\n{addition}"


def build_user_prompt(snapshot: dict[str, Any], headlines: list[str]) -> str:
    lines = ["Today's market data:"]
    for row in snapshot.get("series") or []:
        label = row.get("label", "")
        price = row.get("price")
        change = row.get("change_pct")
        price_s = "n/a" if price is None else str(price)
        change_s = "n/a" if change is None else f"{change}%"
        lines.append(f"- {label}: {price_s} ({change_s})")

    lines.append("")
    lines.append("Top headlines:")
    for i, headline in enumerate(headlines[:5], start=1):
        lines.append(f"{i}. {headline}")

    lines.append("")
    lines.append("Write a morning market brief based on the above.")
    return "\n".join(lines)


def build_persona_badge(profile: dict[str, Any] | None) -> str | None:
    if not profile:
        return None
    tier = TIER_SHORT.get(profile.get("tier", ""), profile.get("tier", ""))
    goal = profile.get("goal", "")
    geo = GEO_SHORT.get(profile.get("geography", ""), profile.get("geography", ""))
    parts = [p for p in (goal, tier, geo) if p]
    return " | ".join(parts) if parts else None


def _strip_markdownish(text: str) -> str:
    cleaned = text.replace("**", "").replace("__", "").strip()
    return cleaned


def generate_brief(
    snapshot: dict[str, Any],
    headlines: list[str],
    profile: dict[str, Any] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Return {ok, text, badge}. Never raises; never exposes exception text."""
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    badge = build_persona_badge(profile)

    if not key:
        logger.warning("ANTHROPIC_API_KEY missing; returning safe brief message")
        return {
            "ok": False,
            "text": BRIEF_UNAVAILABLE_USER_MESSAGE,
            "badge": badge,
        }

    try:
        client = Anthropic(api_key=key)
        message = client.messages.create(
            model=MODEL,
            temperature=TEMPERATURE,
            system=build_system_prompt(profile),
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(snapshot, headlines),
                }
            ],
            max_tokens=2048,
        )
        chunks: list[str] = []
        for block in message.content:
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
        narrative = _strip_markdownish("\n\n".join(chunks).strip())
        if not narrative:
            return {
                "ok": False,
                "text": BRIEF_UNAVAILABLE_USER_MESSAGE,
                "badge": badge,
            }
        return {"ok": True, "text": narrative, "badge": badge}
    except Exception:
        logger.exception("Claude brief generation failed")
        return {
            "ok": False,
            "text": BRIEF_UNAVAILABLE_USER_MESSAGE,
            "badge": badge,
        }
