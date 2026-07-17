"""Curated static headlines used when Finnhub is unavailable.

Frozen from a typical general/forex news set for demo resilience.
Refresh periodically; ≤ ~1 day old is acceptable per PRD.
"""

FALLBACK_HEADLINES: list[dict[str, str]] = [
    {
        "title": "Asian equities mixed as investors weigh growth and rate outlook",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Dollar holds steady against Singapore dollar amid regional flows",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Gold remains supported as markets watch geopolitical risk",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Oil prices firm on supply concerns and demand signals",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Global investors eye Fed path and Asia earnings season",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Hang Seng rises on China stimulus hopes",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Nikkei under pressure as yen strength weighs on exporters",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "US futures soft ahead of key inflation prints",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "Brent edges higher on Middle East supply risk",
        "url": "https://finnhub.io/news",
    },
    {
        "title": "SGD tracks regional FX as risk appetite firms",
        "url": "https://finnhub.io/news",
    },
]
