"""DeepSeek morning-brief generation with graceful degradation."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

BRIEF_UNAVAILABLE_USER_MESSAGE = (
    "Brief temporarily unavailable. Please try again."
)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
TEMPERATURE = 0.4

V1_SYSTEM_PROMPT = """You are a senior wealth analyst writing a morning market brief for a private banking client.
Write in clear, professional English. Be concise — 2 paragraphs in the BRIEF section.
Do not use filler phrases. Lead with what moved and why it matters.
Never fabricate data — only reference the figures provided.
End with one sentence framing the key risk or opportunity for the day.
Do not use markdown formatting.

Return plain text in exactly this labelled structure:
BRIEF:
Two short paragraphs grounded only in the supplied data and headlines.

INVESTMENT_IDEAS:
2 or 3 numbered, concise demo ideas suited to the client profile.

WATCH:
Exactly 3 numbered catalysts or market levels to monitor today, each no more than 12 words.

HOUSE_VIEW:
2 or 3 numbered, simulated research-view observations.

Never describe any generated idea or house view as official OCBC research, advice, or a bank recommendation."""

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
    portfolio_mix = str(profile.get("portfolio_mix") or "").strip()
    if portfolio_mix:
        addition += (
            "\nCurrent portfolio mix (client-provided): "
            f"{portfolio_mix}\nRelate observations to this mix without treating it as verified data.\n"
        )
    return f"{V1_SYSTEM_PROMPT}\n{addition}"


def _headline_title(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("title") or item.get("headline") or "").strip()
    return str(item).strip()


def build_user_prompt(snapshot: dict[str, Any], headlines: list[Any]) -> str:
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
    for i, headline in enumerate(headlines[:10], start=1):
        title = _headline_title(headline)
        if title:
            lines.append(f"{i}. {title}")

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
    return text.replace("**", "").replace("__", "").strip()


def parse_structured_brief_response(raw: str) -> dict[str, list[str]]:
    """Parse the labelled one-call response into renderable sections."""
    marker_to_key = {
        "BRIEF:": "paragraphs",
        "INVESTMENT_IDEAS:": "ideas",
        "WATCH:": "watch",
        "HOUSE_VIEW:": "house_view",
    }
    sections: dict[str, list[str]] = {
        "paragraphs": [],
        "ideas": [],
        "watch": [],
        "house_view": [],
    }
    collected: dict[str, list[str]] = {key: [] for key in sections}
    current = "paragraphs"

    for line in _strip_markdownish(raw).splitlines():
        marker = line.strip().upper()
        if marker in marker_to_key:
            current = marker_to_key[marker]
            continue
        collected[current].append(line.rstrip())

    brief_text = "\n".join(collected["paragraphs"]).strip()
    sections["paragraphs"] = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", brief_text)
        if paragraph.strip()
    ]

    for key in ("ideas", "watch", "house_view"):
        sections[key] = [
            re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            for line in collected[key]
            if line.strip()
        ]
    sections["watch"] = sections["watch"][:3]

    return sections


def _failure_result(badge: str | None) -> dict[str, Any]:
    return {
        "ok": False,
        "text": BRIEF_UNAVAILABLE_USER_MESSAGE,
        "badge": badge,
        "ideas": [],
        "watch": [],
        "house_view": [],
        "email_draft": "",
    }


def build_client_email(brief_text: str) -> str:
    """Wrap a generated brief in the fixed demonstration email template."""
    brief = brief_text.strip()
    return f"""Dear [CLIENT_NAME],

Hope you're doing well. We wanted to share our perspective on the markets today, and what it means for your portfolio.

{brief}

We'd be happy to discuss any next steps.

Thanks,
[RM_NAME]"""


def generate_brief(
    snapshot: dict[str, Any],
    headlines: list[Any],
    profile: dict[str, Any] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Return {ok, text, badge}. Never raises; never exposes exception text."""
    key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY")
    badge = build_persona_badge(profile)

    if not key:
        logger.warning("DEEPSEEK_API_KEY missing; returning safe brief message")
        return _failure_result(badge)

    try:
        # trust_env=False: avoid local HTTP(S)_PROXY 403s to api.deepseek.com
        # (same class of failure as Aircraft Safety Tracker DeepSeek ProxyError).
        http_client = httpx.Client(trust_env=False, timeout=60.0)
        client = OpenAI(
            api_key=key,
            base_url=DEEPSEEK_BASE_URL,
            http_client=http_client,
        )
        # BRIEF, IDEAS, WATCH, and HOUSE_VIEW intentionally share one call.
        # Split WATCH into a second call only if production quality proves poor.
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": build_system_prompt(profile)},
                {
                    "role": "user",
                    "content": build_user_prompt(snapshot, headlines),
                },
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        parsed = parse_structured_brief_response(raw)
        if not parsed["paragraphs"]:
            return _failure_result(badge)
        narrative = "\n\n".join(parsed["paragraphs"])
        return {
            "ok": True,
            "text": narrative,
            "badge": badge,
            "ideas": parsed["ideas"],
            "watch": parsed["watch"],
            "house_view": parsed["house_view"],
            "email_draft": build_client_email(narrative),
        }
    except Exception:
        logger.exception("DeepSeek brief generation failed")
        return _failure_result(badge)
