# PRD: WoW-Aligned Demo Enhancements
**Version:** 1.0  
**Author:** Bhavesh Rajwani  
**Status:** Draft — Interview Prototype Enhancements  
**Depends on:** `tasks/0001-prd-wealth-market-brief-generator.md` (V1/V2 complete)  
**Target Audience:** OCBC AI Lab interview panel (written so a junior developer can implement)  
**Last Updated:** July 2026  
**Changelog:**
- v1.0 — Initial PRD: persona chips, investment ideas, draft email template, what-to-watch, portfolio allocation, house-view card, footer disclaimer, V3 bank-research ingestion path

---

## 1. Introduction / Overview

OCBC WoW (launched July 2026) delivers hyper-personalised wealth experiences to clients via AI avatars. Its five published pillars include: curated news, live market prices, house views with portfolio implications, impact of markets on holdings, and actionable investment ideas by profile.

Our existing prototype already covers live market data, headlines, and persona-aware briefs. This PRD closes the gap toward WoW’s remaining pillars — **as a demonstration content layer**, not as official bank advice.

**Positioning:**
1. **Primary:** Content layer that could feed WoW-style personalisation (same market day → different framing by client).
2. **Secondary:** RM prep tool (fast brief → draft client email → call/message CTAs).

**One-line pitch:** "The RM-side / content-layer complement to OCBC WoW — personalised market narrative, ideas, and a consistent outbound email template — with a clear path to swap LLM-invented research for the bank’s own corpus."

**Critical product rule:** Nowhere in the UI may the app claim that narratives, ideas, house views, or emails are official OCBC recommendations, research, or advice. All generative output is labelled as a **demonstration prototype**.

---

## 2. Goals

1. **Faster demo flow** — Four persona chips so interviewers see personalisation in one click (form still available for custom profiles; Generate remains explicit).
2. **WoW pillar coverage (demo)** — Explicit investment ideas + what-to-watch + optional house-view card + optional portfolio-impact framing.
3. **RM workflow close** — One-click draft client email using a **bank-consistent boilerplate template** wrapping the market brief.
4. **Honest prototype framing** — Persistent footer disclaimer; no “OCBC recommends…” language.
5. **Production path documented** — V3 specifies how proprietary bank research replaces free-form LLM invention via an ingestion/retrieval pipeline.
6. **Stability** — Same graceful-degradation rules as PRD 0001; new panels fail soft.

---

## 3. Target Users

| User | Role in this feature set |
|---|---|
| **Primary demo audience** | OCBC AI Lab interviewers evaluating product + engineering judgment |
| **Primary product user (today)** | Wealth RM preparing for / following up after client contact |
| **End beneficiary (tomorrow)** | WoW / mass-affluent client receiving personalised content (delivery channel not built here) |

---

## 4. User Stories

1. **As an interviewer**, I want one-click persona presets, so I can see “same data, different framing” without filling a long form.
2. **As a wealth RM**, I want to keep the full profile form and press **Generate** myself, so I can customise beyond the presets.
3. **As a wealth RM**, I want 2–3 investment ideas matched to the selected profile, so the brief ends in something actionable (demo of WoW pillar #5).
4. **As a wealth RM**, I want a short “what to watch today” list, so I know catalysts/levels without opening five tabs.
5. **As a wealth RM**, I want a draft client email that wraps today’s brief in a standard bank-style template with placeholders, so the firm can keep outbound tone consistent.
6. **As a wealth RM**, I want an optional rough portfolio mix field, so the narrative can speak to *this* client’s exposures (demo of WoW pillar #4).
7. **As a wealth RM**, I want a clearly labelled **simulated** house-view card, so interviewers see how bank research *would* sit in the UI without implying it is real OCBC research.
8. **As a product owner**, I want a footer disclaimer and a documented V3 ingestion path, so we never over-claim and interviewers see the productionisation story.

---

## 5. Success Metrics (prototype)

| Metric | Target |
|---|---|
| Demo time to first persona switch | < 10 seconds (chip → Generate → brief) |
| Structured panels present | Brief + ideas + what-to-watch + email draft after successful generate |
| Disclaimer visible | Footer on every page load without scrolling past fold optional, but always in footer |
| No official-claim language | Manual copy audit: zero “OCBC recommends / official OCBC view / bank advice” |
| Persona differentiation | 4 chip presets produce visibly different ideas/brief emphasis |
| Stability | Soft-fail any new panel; snapshot never blocked |

---

## 6. Functional Requirements

Implement in **priority order** below. Each FR is done only when acceptance criteria pass.

### Priority 1 — Persona quick-select chips

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-20** | Show **4 persona chips** above the client profile form. | Labels are readable; chips do not auto-submit. |
| **FR-21** | Clicking a chip **pre-fills** the form (tier, goal, assets ≤2, geography) and optionally portfolio mix if that field exists. | Form fields update; user must still press **Generate**. |
| **FR-22** | Keep the full profile form for customisation. | User can edit after chip click; Generate uses final form values. |

**Suggested presets (adjust copy as needed):**

| Chip | Tier | Goal | Assets (≤2) | Geography |
|---|---|---|---|---|
| Conservative HNW · Singapore | High Net Worth | Capital Preservation | Fixed Income, Equities | Singapore-centric |
| Income · Affluent · Asia | Mass Affluent | Income Generation | Fixed Income, Real Assets | Regional Asia |
| Growth · HNW · Global | High Net Worth | Aggressive Growth | Equities, Alternatives | Global |
| Legacy · UHNW · Singapore | Ultra High Net Worth | Legacy Planning | Equities, Real Assets | Singapore-centric |

---

### Priority 2 — Investment ideas panel

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-23** | After a successful generate, show an **Investment ideas** panel with 2–3 short ideas for the active profile. | Ideas visible below or beside the brief; empty/hidden if generate failed. |
| **FR-24** | Ideas are derived from the **same structured LLM response** as the brief (not a separate call). | One DeepSeek call returns brief + ideas (+ other structured blocks). |
| **FR-25** | Panel chrome must **not** imply official OCBC product recommendations. | e.g. heading “Investment ideas (demo)” or similar; no “OCBC recommends”. |

---

### Priority 3 — Draft client email (template + brief)

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-26** | After successful generate, show **Draft email to client** with Copy. | Copy puts the full email text on the clipboard. |
| **FR-27** | Email body uses a **fixed boilerplate** wrapping the market brief (same LLM call / parsed brief text — **not** a second free-form email generation). | Boilerplate is consistent every time; only the brief section changes with market/persona. |
| **FR-28** | Boilerplate includes clear placeholders: `[CLIENT_NAME]`, `[RM_NAME]`. | Placeholders visible so interviewers see the bank can standardise the template. |

**Canonical template (implement exactly unless product owner tweaks wording):**

```text
Dear [CLIENT_NAME],

Hope you're doing well. We wanted to share our perspective on the markets today, and what it means for your portfolio.

<MARKET_BRIEF_PARAGRAPHS_HERE>

We'd be happy to discuss any next steps.

Thanks,
[RM_NAME]
```

**Note:** A one-line footer under the draft may say: “Template for demo only — not an official OCBC communication.”

---

### Priority 4 — What to watch today

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-29** | Show **What to watch today** with exactly 3 short bullets (≤ ~12 words each) after successful generate. | Always 3 items when ok; hidden or fallback message when parse/LLM fails. |
| **FR-30** | Prefer **same structured LLM response** as brief/ideas (Priority 2). Only split to a separate call if output quality is poor in practice. | Default implementation = one call; document fallback path in code comments / README. |

---

### Priority 5 — Portfolio allocation field (WoW pillar #4 demo)

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-31** | Add optional **rough portfolio mix** to the profile form (free text, e.g. `60% equities / 30% bonds / 10% gold`). | Completable in seconds; empty is allowed. |
| **FR-32** | When present, include mix in the LLM prompt so the brief can mention exposure implications. | With mix filled, brief references it; without mix, behaviour unchanged from PRD 0001. |
| **FR-33** | Persona chips may pre-fill a sample mix string. | Optional; if used, still editable before Generate. |

---

### Priority 6 — Simulated house-view card (WoW pillar #3 demo)

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-34** | Show a card titled clearly as **simulated / demo** house view (e.g. “Simulated research view (demo) — not OCBC official research”). | Title must include demo/not-official wording. |
| **FR-35** | Card shows 2–3 short bullets from the same structured LLM response (or static demo bullets if LLM block missing). | Soft-fail: card can hide or show static placeholder; never crash. |

---

### Priority 7 — Footer disclaimer (all pages)

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-36** | Persistent **page footer** on the main UI with prototype disclaimer. | Visible without needing a modal; present on `GET /`. |

**Required meaning (wording may be tightened, but must include):**
- This is a **demonstration prototype** for interview / AI Lab purposes.
- Market figures come from public data providers; narrative and ideas are **AI-generated for demo**.
- **Nothing here is official OCBC research, advice, or a bank recommendation.**
- In production, the bank could restrict generation to **approved proprietary research** via an ingestion pipeline (see §10 V3).

---

### Cross-cutting (this PRD)

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-37** | Structured LLM output contract: parse labelled blocks from one response (see §8). | Unit tests cover happy parse + missing-block soft-fail. |
| **FR-38** | No UI string claims official OCBC endorsement of generated content. | Copy review checklist in README or PR description. |
| **FR-39** | Graceful degradation: snapshot + existing brief rules from PRD 0001 still apply; new panels fail soft. | LLM failure → safe brief message; ideas/watch/house/email draft hidden or marked unavailable. |

**Junior build order:** FR-20–22 → FR-23–25 + FR-37 → FR-26–28 → FR-29–30 → FR-36 → FR-31–33 → FR-34–35 → FR-38–39 polish → §10 V3 design notes in README (no full pipeline build unless explicitly scheduled).

---

## 7. Non-Goals (Out of Scope for this PRD’s build)

1. Real OCBC research PDFs, house views, or product shelves.
2. Live portfolio custody feeds or KYC/CRM integration.
3. Sending email/SMS for real (mailto/sms placeholders / copy only).
4. Side-by-side dual-persona comparison layout.
5. Audio / podcast brief.
6. Avatars (Wendy/Wayne) or voice UI.
7. Building the full V3 ingestion pipeline in this sprint (design + interface only unless product owner expands scope).
8. Claiming regulatory suitability or personalised advice status.

---

## 8. Design Considerations

- Preserve OCBC red/white system from PRD 0001 (`#e1241c` brand; `#dc2626` only for ↓ moves).
- Chips: secondary/outline style; active chip highlighted; do not look like primary CTAs competing with **Generate**.
- Panels: Investment ideas / What to watch / House view as simple sections — avoid dashboard clutter.
- Draft email: monospace or plain preformatted block + Copy button.
- Footer: muted small text; always present.

### Suggested one-call LLM structure

Ask the model to return **plain text** with clear markers (no markdown), for example:

```text
BRIEF:
...paragraphs...

INVESTMENT_IDEAS:
1. ...
2. ...
3. ...

WATCH:
1. ...
2. ...
3. ...

HOUSE_VIEW:
1. ...
2. ...
```

App parses markers → renders panels. Email template wraps **BRIEF** body only (FR-27).

If structured quality is weak in practice, fall back to: brief+ideas+house in one call; WATCH as a second call or static fallback (document the decision in JOURNAL).

---

## 9. Technical Considerations

- Stack unchanged: FastAPI + Jinja2/HTMX + DeepSeek + yfinance + Finnhub.
- Prefer extending `llm/brief.py` + brief partial template; avoid new services unless needed.
- Persona chips: client-side JS fill + existing `POST /generate`.
- Portfolio mix: new optional form field; include in prompt builder.
- Tests: extend `tests/test_brief.py` (prompt + parser) and `tests/test_routes.py` (panels present / soft-fail).
- Do not re-fetch yfinance on Generate (PRD 0001 FR-12 still holds).

---

## 10. V3 — Bank proprietary research ingestion (design now; build later)

### 10.1 Problem

Demo content is LLM-synthesised from public market data + headlines. That is fine for an interview prototype, but **unsafe / non-compliant** if presented as bank advice. Production needs generation **grounded only in approved materials**.

### 10.2 Goal

Replace free-form “invented” ideas/house views with retrieval over **bank-approved** research, model portfolios, and compliance-cleared narratives. The LLM reformats and personalises; it does **not** invent official recommendations.

### 10.3 High-level pipeline

1. **Ingest** — Approved PDFs / CMS exports / research API → text extraction.
2. **Chunk + metadata** — Document id, date, asset class, geography, risk rating, product codes, expiry/withdraw date.
3. **Index** — Embeddings + metadata filters (tier, geography, asset focus).
4. **Retrieve at generate time** — Top-k chunks constrained by client profile + filters.
5. **Generate with citations** — Prompt: “Use only the provided excerpts; if insufficient, say so.” Output includes source ids.
6. **Guardrails** — Blocklist phrases (“guaranteed return”); refuse when retrieval empty; human-in-the-loop for outbound email.
7. **Audit** — Log profile, retrieved doc ids, model version, timestamp for compliance review.

### 10.4 Interface stub (for future code)

```text
ResearchSource.retrieve(profile, market_context) -> list[Passage]
Passage: { id, title, excerpt, as_of, url_or_doc_id }
```

Demo today: `ResearchSource` may return empty or simulated passages labelled demo. Production: only bank corpus.

### 10.5 What interviewers should hear

> “Today the model proposes demo ideas from public data. For production we’d ingest OCBC research, retrieve by client profile, and generate only from that corpus — same UI, different trust boundary.”

---

## 11. Success / Acceptance (overall)

This PRD is complete when:
- [ ] FR-20–39 implemented or explicitly deferred with owner sign-off
- [ ] Footer disclaimer live
- [ ] Demo script works: chip → tweak form (optional) → Generate → brief + ideas + watch + email copy
- [ ] Copy audit: no official OCBC recommendation claims
- [ ] README documents V3 ingestion path (§10)
- [ ] Tests cover structured parse + soft-fail

---

## 12. Open Questions

1. Exact chip label copy — keep suggested table or bank-preferred naming?
2. Should `[CLIENT_NAME]` / `[RM_NAME]` be editable fields on the page, or placeholders only?
3. House view: always LLM-simulated, or ship with 3 frozen static demo bullets for reliability?
4. When do we schedule V3 ingestion spike (post-interview vs before)?
5. Expand market series toward WoW’s “7 → 12” roadmap in a later PRD?

---

## 13. Demo narrative (suggested)

1. Open live URL — snapshot + auto V1 brief + footer disclaimer.
2. Click **Growth · HNW · Global** chip → press **Generate** — badge + different ideas.
3. Click **Conservative HNW · Singapore** → Generate again — same numbers, defensive framing.
4. Copy **Draft email** — show template + placeholders.
5. Point to footer + one sentence on V3: “Swap demo generation for OCBC research retrieval.”

---

## 14. References

- OCBC WoW public launch materials (July 2026) — five feature pillars
- `tasks/0001-prd-wealth-market-brief-generator.md` — base product
- `Planning/demo-enhancement-ideas.md` — earlier idea backlog
- Competitive patterns: BriefVault / FN2 / Briefr (personalised morning brief); Morgan Stanley Debrief (RM outbound draft); Bloomberg ASKB workflows (scheduled briefs) — inspirations only, not feature parity
