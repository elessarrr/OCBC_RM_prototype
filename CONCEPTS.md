# Concepts

> Shared domain vocabulary for Wealth Morning Brief. Glossary only — not a full spec. Accretes as compound learnings are written.

## Entities

### Market snapshot

The set of eight series shown on page load: STI, S&P 500, Hang Seng, Nikkei, USD/SGD, Gold, Brent, US 10Y Yield. Each cell has price, day change (points + %), and directional arrow. Includes an `"as of"` timestamp (SGT).

### Headline set

Short list of financial headlines used as LLM context and shown under TOP HEADLINES. Prefer live Finnhub; fall back to curated static headlines when Finnhub fails.

### Morning brief

Plain-paragraph DeepSeek narrative synthesised from the **provided** snapshot + headlines only. Must not invent prices or news. V1 is generic; V2 is persona-aware.

### Client profile (V2)

Four intake fields: wealth tier, primary financial goal, asset class focus (max 2), geography. Drives prompt tone/emphasis and the persona badge.

### Persona badge

Compact label on the brief (e.g. `Capital Preservation | HNW | Singapore Focus`) when a V2 profile was used.

## Status concepts

### Last close

When markets are shut (weekend / after hours), yfinance values are the previous session close — not live ticks and not invented. Always show `"as of [timestamp]"`.

### Graceful LLM degradation

Snapshot and headlines render independently of DeepSeek. If the LLM call fails, the brief region shows a safe fixed message; the page never crashes or blanks.

### Snapshot reuse

On persona regenerate, the app keeps the current in-page market numbers and only changes the narrative/badge. Explicit market refresh is separate (`GET /market` or full reload).

## Evaluation concepts

### LLM-as-judge

Using an LLM to score another LLM's output (e.g. RAGAS faithfulness/relevance). The judge **must be a different model from the generator** — same-model scoring is self-evaluation bias. Even done right (independent, larger judge; bigger dataset) it stays *directional* without human-labeled ground truth. Applies if we ever auto-score the morning brief. See `docs/solutions/best-practices/independent-llm-judge-for-eval.md`.

## Named processes

### Auto-generate (V1)

On page load, after the snapshot paints, the brief region loads with a spinner and requests a DeepSeek narrative without a user click.

### Finnhub fallback

On Finnhub timeout/error, serve frozen static headlines (acceptable if ≤ ~1 day old) so the demo continues.

### Compound capture

After a non-trivial fix: write `docs/solutions/...`, validate frontmatter, append `JOURNAL.md`, link-only bullet in `LEARNINGS.md` § Proactive Prevention when the pattern may recur.
