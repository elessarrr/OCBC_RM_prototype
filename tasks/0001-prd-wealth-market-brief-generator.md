# PRD: Personalised Wealth Market Brief Generator
**Version:** 1.3  
**Author:** Bhavesh Rajwani  
**Status:** Draft — Interview Prototype  
**Target Audience:** OCBC AI Lab interview panel (also written so a junior developer can implement)  
**Last Updated:** July 2026  
**Changelog:**
- v1.3 — No hard max-token cap (quality over length); paid Railway → no warmup/cold-start mitigation required
- v1.2 — Moved to `tasks/0001-…`; added Goals, RM user stories, numbered FRs + junior checklist, resolved product decisions
- v1.1 — UI colour system updated to OCBC brand identity (red/white, not navy)

---

## 1. Introduction / Overview

Wealth relationship managers (RMs) at banks like OCBC spend 30–60 minutes each morning manually compiling market updates before client calls. This time is wasted on aggregation, not advice. Meanwhile, mass affluent customers — those below the private banking threshold — receive generic market emails that feel impersonal and are rarely read.

OCBC's OCBC WoW platform (launched July 2026) bets on AI-powered, hyper-personalised wealth delivery at scale. The upstream gap: how do you generate a brief that is genuinely personalised to a specific client's wealth tier, goals, and preferences — not just a reformatted Bloomberg digest?

**This prototype answers that question** with a live tool that pulls real market data and headlines, then generates a morning brief (generic in V1; persona-aware in V2).

**One-line pitch:** "The content layer that makes OCBC WoW feel personal, not generic."

---

## 2. Goals

1. **Fresh market data** — Show same-day (or last-close when markets are shut) figures for the seven tracked series, clearly timestamped.
2. **Reality-grounded narrative** — The LLM brief must only reference figures and headlines supplied by the app; never invent prices, moves, or news.
3. **Fast prep for RMs** — End-to-end brief generation in under 10 seconds so an RM can use it before a client call.
4. **Visible personalisation (V2)** — Same market snapshot, meaningfully different briefs across client profiles.
5. **Demo-stable** — Page always shows the market snapshot; LLM/news failures degrade gracefully (never blank or crash).

---

## 3. Target Users

| User | Context |
|---|---|
| **Primary product user:** Wealth RM | Uses brief as prep before a client call |
| **Demo audience:** OCBC interviewer | Evaluates product thinking + technical execution |
| **End beneficiary:** Mass affluent client | Receives personalised brief via app or RM (future delivery channel; not built here) |

---

## 4. User Stories (RM-focused)

1. **As a wealth RM**, I want a same-day market snapshot (indices, FX, gold, oil) when I open the page, so I can see what moved before I call a client.
2. **As a wealth RM**, I want an auto-generated plain-language morning brief grounded in those figures and today’s headlines, so I spend less time aggregating and more time advising.
3. **As a wealth RM**, I want to set a client’s wealth tier, goal, asset focus, and geography, so the brief is framed for *that* client’s job-to-be-done — not a generic blast.
4. **As a wealth RM**, I want to regenerate the brief for a different client profile without losing the current market numbers, so I can compare how the same day looks for two clients.
5. **As a wealth RM**, I want the page to still show market data (and a clear fallback message) if news or the LLM fails, so a flaky API never blocks my prep.

---

## 5. Success Metrics (prototype)

| Metric | Target |
|---|---|
| Brief generation time | < 10 seconds end-to-end |
| Data freshness | Same-day when markets trade; otherwise last close with `"as of [timestamp]"` |
| Persona differentiation | Output visibly, meaningfully different across 3+ persona combinations |
| Demo stability | Zero crashes during a 10-minute walkthrough |
| "Would you use this?" | Yes from at least one interviewer |

---

## 6. Functional Requirements

Use this as the **junior developer checklist**. Implement in order. Each item is done only when its acceptance criteria pass.

### V1 — Live data + auto brief

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-1** | On `GET /`, fetch all 7 yfinance series and render the market snapshot. | STI, S&P 500, Hang Seng, Nikkei, USD/SGD, Gold, Brent each show price, day change (points + %), and ↑ / ↓ / →. Labels match §8. |
| **FR-2** | Show an `"as of [timestamp]"` (SGT) on the snapshot. | Timestamp visible; when markets are closed/weekend, values are **last close**, not blank or invented. |
| **FR-3** | Fetch Finnhub general + forex news; show top headlines on the page. | At least 3 headlines render under TOP HEADLINES when Finnhub succeeds. |
| **FR-4** | If Finnhub times out or errors, use curated **static fallback headlines** (≤ 1 day old is OK). | Page still loads; headlines section shows fallback; no crash; optional subtle note that headlines are cached/fallback. |
| **FR-5** | **Auto-generate** the V1 LLM brief on page load (no button required). | After snapshot paints, brief section shows spinner then narrative without user click. |
| **FR-6** | Claude brief uses only provided market figures + headlines; plain paragraphs; no markdown. | Output is 2–3 paragraphs; no `**`, bullets, or headers; no prices/facts not in the prompt payload. |
| **FR-7** | **Graceful LLM degradation:** market snapshot never waits on Claude; brief failure shows a safe user message. | Snapshot visible even if Claude is down; brief area shows e.g. "Brief temporarily unavailable. Please try again." — never raw exception text or API keys. |
| **FR-8** | Loading UX while Claude runs. | Spinner (`#e1241c`) + "Generating your brief…"; after 15s add "This is taking a moment — almost there." |
| **FR-9** | `GET /market` returns JSON snapshot (for refresh). | Valid JSON with the 7 series + timestamp; used by optional refresh control. |
| **FR-10** | Optional `GET /health` returns a cheap OK response. | Nice-to-have liveness probe; **not** required for demo warmup (paid Railway). Must not call yfinance/Finnhub/Claude. |

### V2 — Persona-aware brief

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-11** | Client profile form: wealth tier, primary goal, asset focus (multi-select **max 2**), geography (single). | Completable in < 30s; validation blocks > 2 asset classes. |
| **FR-12** | `POST /generate` accepts profile + uses **current in-page market snapshot** (does not re-fetch markets by default). | Regenerating for a new persona keeps identical numbers; only narrative/badge change. Explicit market refresh is separate (`/market` or reload). |
| **FR-13** | V2 system prompt appends tier/goal/assets/geography guidance (§10). | V1 and V2 briefs may be similar length; **no hard max-token cap** — allow enough tokens for a good answer. |
| **FR-14** | Persona badge on the brief (e.g. `Capital Preservation \| HNW \| Singapore Focus`). | Badge visible whenever a V2 profile was used. |
| **FR-15** | Three distinct persona combos → meaningfully different briefs from the same market data. | Manual check on Day 2; RM can tell which client the brief is for without reading the form. |
| **FR-16** | Copy button copies brief text to clipboard. | One click; works on desktop demo browser. |

### Cross-cutting

| ID | Requirement | Acceptance criteria |
|---|---|---|
| **FR-17** | Secrets only via `.env` / Railway env (`ANTHROPIC_API_KEY`, `FINNHUB_API_KEY`). | No keys in git; `.env.example` lists names without values. |
| **FR-18** | UI follows §11 colour system (OCBC red/white; loss red only on ↓ cells). | Header/CTA brand red `#e1241c`; down moves `#dc2626` + ↓. |
| **FR-19** | Mobile-responsive single page; title "Wealth Morning Brief — AI Lab Prototype"; no OCBC logo. | Usable on phone/tablet for demo. |

**Junior build order:** FR-1 → FR-2 → FR-3/4 → FR-5–8 → FR-9–10 → deploy → FR-11–16 → FR-17–19 polish.

---

## 7. Scope Summary

### V1 — Live Data Pull (build first)

**Does:** Live (or last-close) snapshot, headlines, auto LLM narrative, graceful fallbacks.  
**Does not:** Login, client profile, personalisation.

**Definition of done:** FR-1–10 pass; shareable URL; 5-minute demo without refresh gymnastics.

### V2 — Client Persona-Aware Brief (after V1 stable)

**Adds:** Form, persona prompt, badge, HTMX regenerate, copy.  
**Definition of done:** FR-11–16 pass; non-technical interviewer can operate unaided.

---

## 8. Product Decisions (resolved)

| Topic | Decision |
|---|---|
| Brief on load | **Auto-generate** on page load (V1). V2 form triggers regenerate via `POST /generate`. |
| LLM / news failure | **Graceful degradation:** snapshot always renders; brief/headlines use safe fallbacks (same pattern as Aircraft Safety Tracker AI summary — never block the page on LLM I/O). |
| Markets closed / weekend | Show **last close** + `"as of [timestamp]"`. Do not invent live moves. |
| Finnhub fallback freshness | Static curated headlines OK if **≤ ~1 day old**. |
| Persona regenerate vs market refresh | Persona change **reuses** the current snapshot (demo insight: same data, different framing). Re-fetch markets only on full page load or explicit refresh. |
| Output length / tokens | **No hard max-token limit.** Aim for a good answer; V1 and V2 can be similar length. Prompt still asks for concise 2–3 paragraphs — quality over artificial truncation. |
| Railway hosting | **Paid Railway** — no sleep/cold-start warmup ritual required for demo. Optional `/health` only if useful for ops. |

---

## 9. Data Sources

### Market Data (via `yfinance` — free, no API key)

| Data Point | Symbol | Display Label |
|---|---|---|
| Straits Times Index | `^STI` | STI |
| S&P 500 | `^GSPC` | S&P 500 |
| Hang Seng Index | `^HSI` | Hang Seng |
| Nikkei 225 | `^N225` | Nikkei |
| USD/SGD | `USDSGD=X` | USD/SGD |
| Gold | `GC=F` | Gold (USD/oz) |
| Brent Crude | `BZ=F` | Brent Crude |

**Display format:** Current / last-close price + day change (points and %) + directional arrow (↑ ↓ →)

**Why yfinance over Finnhub for market data:** yfinance covers SGX and Asian indices on the free tier. Finnhub free tier is US-centric for international indices.

---

### News (via Finnhub — free tier, API key required)

| Feed | Finnhub Endpoint | Purpose |
|---|---|---|
| General market news | `/news?category=general` | Top headlines for narrative context |
| Forex news | `/news?category=forex` | USD/SGD and regional FX context |

**Free tier limits:** 60 API calls/minute — fine for demo.

**Fallback:** Curated static headlines (≤ 1 day old OK). Never let Finnhub timeout crash the demo.

---

### LLM (Claude API via Anthropic)

- Model: `claude-sonnet-4-6`
- Role: Synthesise **provided** market data + headlines into a narrative (persona-aware in V2)
- Max tokens: **no hard cap** — use whatever is needed for a good brief (prompt still targets concise 2–3 paragraphs; V1/V2 length may be similar)
- Temperature: 0.4
- Hard rule: never fabricate figures or headlines not in the prompt

---

## 10. V2 Client Intake Form

Four fields. Complete in under 30 seconds.

### Field 1: Wealth Tier
| Option | Description | Brief Tone |
|---|---|---|
| Mass Affluent | SGD 200K–2M investable assets | Plain language, practical, action-oriented |
| High Net Worth | SGD 2M–20M investable assets | More sophisticated, product-aware, slightly more formal |
| Ultra High Net Worth | SGD 20M+ investable assets | Concise, strategic, assumes financial literacy |

### Field 2: Primary Financial Goal
| Option | LLM Emphasis |
|---|---|
| Capital Preservation | Volatility, downside risk, defensive assets, USD/SGD stability |
| Income Generation | Dividend-paying indices, bond proxies, REITs, yield context |
| Aggressive Growth | Momentum, growth sectors, high-beta moves |
| Legacy / Estate Planning | Long-term structural themes, geopolitical context, low-noise framing |

### Field 3: Asset Class Focus
Multi-select (up to 2): Equities (Singapore / Asia), Global Equities, Fixed Income / Bonds, Real Assets (Property, REITs, Infrastructure), Commodities, Cash / FX

### Field 4: Geography Focus
Single select: Singapore-centric, Regional Asia, Global

---

## 11. LLM Prompt Architecture

### V1 System Prompt
```
You are a senior wealth analyst writing a morning market brief for a private banking client.
Write in clear, professional English. Be concise — 2 paragraphs, no bullet points.
Do not use filler phrases. Lead with what moved and why it matters.
Never fabricate data — only reference the figures provided.
End with one sentence framing the key risk or opportunity for the day.
```

### V1 User Prompt (constructed dynamically)
```
Today's market data:
- STI: {value} ({change}%)
- S&P 500: {value} ({change}%)
- Hang Seng: {value} ({change}%)
- Nikkei: {value} ({change}%)
- USD/SGD: {value} ({change}%)
- Gold: {value} ({change}%)
- Brent Crude: {value} ({change}%)

Top headlines:
1. {headline_1}
2. {headline_2}
3. {headline_3}

Write a morning market brief based on the above.
```

### V2 System Prompt Addition (appended after V1 system prompt)
```
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
```

---

## 12. UI Specification

### Layout (single page, no navigation)

```
┌─────────────────────────────────────────────────┐
│  Wealth Morning Brief — AI Lab Prototype  [date] │
├─────────────────────────────────────────────────┤
│  MARKET SNAPSHOT                    as of [ts]   │
│  STI … | S&P … | HSI … | N225 …                 │
│  USD/SGD … | Gold … | Brent …                   │
├─────────────────────────────────────────────────┤
│  [V2 ONLY] CLIENT PROFILE                        │
│  … form fields…  [Generate My Brief]             │
├─────────────────────────────────────────────────┤
│  TODAY'S BRIEF                           [Copy]  │
│  [Persona badge — V2 only]                       │
│  [LLM narrative or safe fallback]                │
│  TOP HEADLINES                                   │
└─────────────────────────────────────────────────┘
```

### Visual Design Principles
- Clean, bank-appropriate. Not flashy.
- **Red and white** (OCBC digital aesthetic). Do **not** use navy (DBS territory).
- Mobile-responsive. No OCBC logo. Font: Inter or system-ui. Brief output: plain paragraphs only.

### Colour System

| Element | Colour | Hex | Notes |
|---|---|---|---|
| Page background | White | `#FFFFFF` | |
| Header bar | OCBC Red | `#e1241c` | |
| Header text | White | `#FFFFFF` | |
| Body / card text | Charcoal | `#1a1a1a` | |
| Card / panel background | Light grey | `#f5f5f5` | |
| Border / divider | Light grey | `#e5e5e5` | |
| CTA button | OCBC Red | `#e1241c` | White label |
| CTA hover | Dark red | `#b81c15` | |
| Persona badge bg | Red tint | `#fef2f2` | |
| Persona badge text | Dark red | `#991b1b` | |
| Positive (↑) | Green | `#16a34a` | |
| Negative (↓) | Loss red | `#dc2626` | Distinct from brand red |
| Flat (→) | Grey | `#6b7280` | |
| Spinner | OCBC Red | `#e1241c` | |
| Link | Dark red | `#991b1b` | |

**Red conflict:** Brand red = chrome (header, CTA). Loss red = snapshot ↓ cells only.

### Loading State
- Snapshot first; spinner under brief until LLM returns (or fallback message).
- After 15s: "This is taking a moment — almost there."

---

## 13. Technical Architecture

### Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | FastAPI (Python) | Fast, async-native |
| Market data | yfinance | Free, Asian indices |
| News | Finnhub REST | Free tier OK |
| LLM | Anthropic Claude | Narrative quality |
| Frontend | Jinja2 + HTMX | No build step; form POST without full reload |
| Deployment | Railway (paid) | Existing account; no free-tier sleep/warmup needed |

### Why not Streamlit / React?
Streamlit looks like a notebook; React is overkill for a 3-day build.

### File Structure
```
wealth-brief/
├── main.py              # FastAPI app
├── data/
│   └── market.py        # yfinance + Finnhub (+ static headline fallback)
├── llm/
│   └── brief.py         # Prompt construction + Claude (graceful errors)
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── .env                 # not committed
├── .env.example
├── requirements.txt
├── Procfile
└── README.md
```

### Key Endpoints
```
GET  /           # Page + live/last-close market data; kicks off auto brief (V1)
POST /generate   # Persona-aware brief (V2); reuses current snapshot unless client sends fresh market payload
GET  /market     # JSON market snapshot (refresh)
GET  /health     # Optional liveness (no external API calls); not required for paid Railway demo
```

---

## 14. Build Plan (3–4 Days)

### Day 1 — V1 Working
- [ ] FastAPI skeleton + `market.py` (FR-1, FR-2)
- [ ] `index.html` snapshot (FR-1)
- [ ] Finnhub + fallback (FR-3, FR-4)
- [ ] `brief.py` + auto-generate + degradation (FR-5–8)
- [ ] `/market` (FR-9); optional `/health` (FR-10)
- [ ] CSS + spinner; deploy Railway (paid)

**V1 done when:** Public URL; snapshot always shows; brief or safe fallback; phone demo works.

### Day 2 — V2 Profile Form
- [ ] Form + HTMX → `/generate` (FR-11, FR-12)
- [ ] V2 prompt + badge (FR-13, FR-14)
- [ ] Test 3–6 personas (FR-15); README + public repo

### Day 3 — Polish + Demo Prep
- [ ] Copy button (FR-16); stress 10 generations; Finnhub fallback verified
- [ ] Run demo narrative 3×

### Day 4 — Buffer / optional SME pre-screener scaffold

---

## 15. Demo Narrative (Interview Walkthrough)

Practice under 5 minutes. Do not read from notes.

**Opening (30s):** Tie to OCBC WoW hyper-personalisation; this prototype is the content layer.

**V1 (60s):** Live yfinance snapshot + auto Claude brief from real figures/headlines (~8s). Read first sentence aloud.

**V2 (90s):** HNW / Capital Preservation / Fixed Income / Singapore → generate. Then Mass Affluent / Aggressive Growth / Equities / Global. Same numbers, different job-to-be-done.

**Pitch (60s):** Mass affluent retention/cross-sell; personalised brief via app or RM.

**Close (30s):** V3 = holdings-aware moves; V2 already pilot-worthy pending DS validation.

---

## 16. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| yfinance stale when market closed | Medium | Last close + `"as of [timestamp]"` |
| Finnhub timeout | Medium | Static headlines ≤ 1 day old |
| Claude down / slow | Medium | Snapshot first; safe brief message; spinner + 15s copy |
| Brief hallucinates | Medium | Prompt: only use provided figures; spot-check generations |
| Persona briefs too similar | Medium | Day 2 prompt tuning; FR-15 gate |

---

## 17. What This Demonstrates to the Interviewer

| JD Requirement | How this prototype shows it |
|---|---|
| Rapid AI prototyping | 3-day build, Railway URL |
| Build and iterate with modern AI tools | V1 → V2 iteration |
| Validate ideas through working solutions | Live demo in the room |
| Translate business needs into technical direction | Tied to OCBC WoW |
| Stay current with emerging tech | Claude, yfinance, HTMX — pragmatic |
| Production-minded prototypes | FastAPI; V3 called out as next decision |
| Bridge business, product, engineering | Demo: data → client need → revenue |

---

## 18. Non-Goals (Out of Scope)

- User authentication / login
- Persistent client profiles
- Holdings integration (V3 in demo narrative)
- Push notifications
- Multi-language support
- OCBC branding or internal data access
- Fine-tuning or custom model training

---

## 19. Open Questions

None blocking build. Revisit only if needed:

1. Exact wording of the static Finnhub fallback headline set (curate on Day 1 from real Finnhub output, then freeze).

---

*Working document. Update as the build progresses. Canonical path: `tasks/0001-prd-wealth-market-brief-generator.md`.*
