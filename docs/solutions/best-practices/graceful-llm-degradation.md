---
title: Graceful LLM degradation keeps market snapshot usable
date: 2026-07-13
category: best-practices
module: llm-brief
problem_type: best_practice
component: llm_brief
severity: high
applies_when:
  - "Claude or Anthropic API is slow, down, or misconfigured"
  - "Building or reviewing GET / or POST /generate brief UX"
tags: [llm, graceful-degradation, demo-stability, anthropic]
---

# Graceful LLM degradation keeps market snapshot usable

## Context

Interview demos fail when a blank page or stack trace appears because Claude timed out. Aircraft Safety Tracker taught the same lesson for DeepSeek summaries: treat LLM I/O as unreliable.

## Guidance

1. Render the **market snapshot** (and headlines) without waiting on Claude.
2. Show a spinner in the brief region only; after failure, show a **fixed safe message** (e.g. "Brief temporarily unavailable. Please try again.").
3. Never pass exception text, status codes, or API key fragments to the template.
4. Catch auth, connection, and generic API errors in `llm/brief.py` and map them all to that safe message.
5. Apply the same idea to Finnhub: static headline fallback so news failure cannot block the page.

## Why This Matters

Demo stability and RM trust: numbers still appear even when the narrative layer fails.

## When to Apply

- Any Claude call path (`auto-generate`, `/generate`)
- Any Finnhub fetch path
- Code review of error handling around external APIs

## Examples

- Bad: `except Exception as e: return str(e)` into the brief HTML
- Good: `except Exception: logger.exception(...); return BRIEF_UNAVAILABLE_USER_MESSAGE`

## Related

- PRD FR-7, FR-4 — `tasks/0001-prd-wealth-market-brief-generator.md`
- `LEARNINGS.md` § Proactive Prevention
