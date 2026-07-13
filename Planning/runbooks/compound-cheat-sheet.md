# Compound Cheat Sheet

One page for Wealth Morning Brief. Agents follow `AGENTS.md` + your global User Rule; you use this when you want to understand or override.

---

## The loop (agents run this)

```
START substantive work
  → /learnings-researcher or grep docs/solutions/ + read CONCEPTS.md
  → refresh context/ if snapshot >2 days old
  → do the work
  → if non-trivial fix: write docs/solutions/ doc + validate frontmatter
  → append JOURNAL.md
  → optional LEARNINGS bullet (link only, repeat patterns)
END
```

Skip compound only if user says "skip compound" or the change was trivial (typo, one-liner).

---

## What lives where

| File | Role |
|------|------|
| `docs/solutions/` | Canonical searchable learnings |
| `CONCEPTS.md` | Domain glossary |
| `LEARNINGS.md` | Index + proactive bullets (link to solutions) |
| `JOURNAL.md` | What we did (1–2 sentences) |
| `context/` | Architecture snapshot (not per-task) |
| `.compound/schema.yaml` | Frontmatter contract |
| `.compound/resolution-template.md` | Bug vs knowledge shapes |

---

## Skills

| Skill | When |
|-------|------|
| `/learnings-researcher` | Start of feature/bug work |
| `/compound mode:headless` | End of non-trivial fix |
| `/context-distillation` | `context/` snapshot older than 2 days |
| `/review` | Before landing PR-sized changes |

**Validate:** `python3 .compound/scripts/validate-frontmatter.py docs/solutions/.../file.md`

---

## Seeded solution docs

| Topic | Path |
|-------|------|
| Graceful LLM degradation | `docs/solutions/best-practices/graceful-llm-degradation.md` |

---

## This repo vs Aircraft Safety Tracker

- Same compound loop shape; **no** FAA/NTSB/ASN/gstack requirements here.
- App code lives under `wealth-brief/`; specs under `tasks/`.
