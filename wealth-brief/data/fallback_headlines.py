"""Curated static headlines used when Finnhub is unavailable.

Frozen from a typical general/forex news set for demo resilience.
Refresh periodically; ≤ ~1 day old is acceptable per PRD.
"""

FALLBACK_HEADLINES: list[str] = [
    "Asian equities mixed as investors weigh growth and rate outlook",
    "Dollar holds steady against Singapore dollar amid regional flows",
    "Gold remains supported as markets watch geopolitical risk",
    "Oil prices firm on supply concerns and demand signals",
    "Global investors eye Fed path and Asia earnings season",
]
