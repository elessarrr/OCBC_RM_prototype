"""Turn live market data + news headlines into a personalised morning brief.

Who does what (no coding knowledge needed):
  - The RM fills in the client profile form (tier, goal, geography, etc.) — optional.
  - The app automatically fetches prices and news headlines; the RM does NOT paste headlines.
  - This file builds two text blocks sent to DeepSeek:
      • "system" message = instructions (analyst persona, output format, compliance rules)
      • "user" message   = today's facts (prices + headline titles) — auto-assembled by code
  - DeepSeek returns one labelled text block; we split it into Brief / Ideas / Watch / House View.
  - If anything fails, the RM sees a friendly "try again" message — never a stack trace.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

# Friendly message shown when the AI service is down or misconfigured.
BRIEF_UNAVAILABLE_USER_MESSAGE = (
    "Brief temporarily unavailable. Please try again."
)

# Which AI model to call and how "creative" it should be (0.4 = mostly factual, still readable).
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
TEMPERATURE = 0.4

# --- Instructions sent to the AI (the "system" message) ---------------------
# V1: base rules every brief must follow — tone, structure, and compliance.
# The AI must reply with these exact section labels so we can split the answer
# into UI panels without a second API call or fragile JSON parsing.
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

# V2: extra instructions when the RM has selected a client profile on the form.
# Injected with tier, goal, asset classes, and geography from the HTMX form.
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

# Short labels for the coloured chip above the brief (e.g. "Aggressive Growth | HNW").
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
    """Build the instruction block (system message) for DeepSeek.

    No profile → generic analyst instructions only (V1).
    With profile → V1 + personalised tone/goal guidance (V2) from the RM's form choices.
    """
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
    # Free-text portfolio mix from the form — context only, not verified bank data.
    portfolio_mix = str(profile.get("portfolio_mix") or "").strip()
    if portfolio_mix:
        addition += (
            "\nCurrent portfolio mix (client-provided): "
            f"{portfolio_mix}\nRelate observations to this mix without treating it as verified data.\n"
        )
    return f"{V1_SYSTEM_PROMPT}\n{addition}"


# Headlines are injected automatically — the RM never types them.
# Chat APIs label the two inputs "system" and "user"; "user" here means "the data
# payload", not "what the human typed". Flow:
#   app fetches headlines (Finnhub or static fallback on page load)
#   → browser posts them hidden in the form as headlines_json
#   → build_user_prompt() turns titles into a numbered list under "Top headlines:"
def _headline_title(item: Any) -> str:
    """Extract the one-line headline text the AI is allowed to reference."""
    if isinstance(item, dict):
        # Normal path: Finnhub returns {"title": "...", "url": "..."}.
        return str(item.get("title") or item.get("headline") or "").strip()
    # Backup path: static fallback headlines may be plain strings.
    return str(item).strip()


def build_user_prompt(snapshot: dict[str, Any], headlines: list[Any]) -> str:
    """Build the facts block (user message) — prices + headlines, assembled by code.

    This is the "ground truth" the AI must not invent beyond:
      • market rows from yfinance (label, price, % change)
      • up to 10 headline titles (URLs stay in the sidebar, not sent to the AI)
    Ends with a one-line instruction to write the brief.
    """
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
    """Small label above the brief showing who it was written for.

    Example: "Aggressive Growth | HNW | Singapore Focus"
    Returns None when no profile was submitted (anonymous demo brief).
    """
    if not profile:
        return None
    tier = TIER_SHORT.get(profile.get("tier", ""), profile.get("tier", ""))
    goal = profile.get("goal", "")
    geo = GEO_SHORT.get(profile.get("geography", ""), profile.get("geography", ""))
    parts = [p for p in (goal, tier, geo) if p]
    return " | ".join(parts) if parts else None


def _strip_markdownish(text: str) -> str:
    """Clean up bold markers the AI sometimes adds despite being told not to."""
    return text.replace("**", "").replace("__", "").strip()


def parse_structured_brief_response(raw: str) -> dict[str, list[str]]:
    """Split the AI's single text reply into the four UI sections.

    Looks for labelled headings: BRIEF:, INVESTMENT_IDEAS:, WATCH:, HOUSE_VIEW:
    Returns a dict with lists: paragraphs, ideas, watch (max 3), house_view.
    """
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
    # Walk line by line; each heading switches which bucket we append to.
    collected: dict[str, list[str]] = {key: [] for key in sections}
    current = "paragraphs"

    for line in _strip_markdownish(raw).splitlines():
        marker = line.strip().upper()
        if marker in marker_to_key:
            current = marker_to_key[marker]
            continue
        collected[current].append(line.rstrip())

    # BRIEF may be one or two paragraphs separated by a blank line.
    brief_text = "\n".join(collected["paragraphs"]).strip()
    sections["paragraphs"] = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", brief_text)
        if paragraph.strip()
    ]

    # Remove leading "1." / "-" from list items so templates render cleanly.
    for key in ("ideas", "watch", "house_view"):
        sections[key] = [
            re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            for line in collected[key]
            if line.strip()
        ]
    sections["watch"] = sections["watch"][:3]

    return sections


def _failure_result(badge: str | None) -> dict[str, Any]:
    """Safe fallback when the AI call fails — same shape as success so the UI never breaks."""
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
    """Pre-fill a demo email the RM could send — placeholders for client and RM names."""
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
    """Main entry point: call DeepSeek once and return all brief panels.

    Inputs (all automatic except profile from the form):
      snapshot  — live prices already on the page
      headlines — news titles already on the page (not typed by the RM)
      profile   — optional client persona from the form

    Returns ok/text/badge/ideas/watch/house_view/email_draft.
    Never crashes the page — errors become the friendly unavailable message.
    """
    key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY")
    badge = build_persona_badge(profile)

    if not key:
        logger.warning("DEEPSEEK_API_KEY missing; returning safe brief message")
        return _failure_result(badge)

    try:
        # Bypass local HTTP proxies that can block api.deepseek.com (403 errors).
        http_client = httpx.Client(trust_env=False, timeout=60.0)
        client = OpenAI(
            api_key=key,
            base_url=DEEPSEEK_BASE_URL,
            http_client=http_client,
        )
        # One API call produces all four sections — cheaper and faster than four separate calls.
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
