# Demo Enhancement Ideas — Wealth Morning Brief

Riffing doc. Mark ideas `[SHIP]`, `[MAYBE]`, `[HOLD]`, or `[SKIP]`.

**Rule:** interview is probably Monday/Tuesday. Two filters before anything ships:
1. Does it make the *demo story* stronger — or just make the app busier?
2. Can it be built + tested + deployed in < 2h without risking what already works?

---

## Decisions confirmed (2026-07-18)

- **Page order:** Brief first → Snapshot (with sentiment) → Profile → Headlines. ✓
- **A3 + A1:** Shipping both. A1 = visual sliding bar 0–100 with fear/greed labels + ⓘ tooltip. ✓
- **UI polish (B1–B6):** On hold — not clear where/how to use them yet.
- **RM contact buttons:** Shipping — big "Call your RM" + "Message your RM" below the brief.

---

## A. Data sources

### A3 — 10-year US Treasury yield `[SHIP]`
**What:** `^TNX` via yfinance. The 10Y is the single most-referenced number in fixed income framing and risk-off narratives.
**Why it's good in a demo:** any Capital Preservation or Fixed Income client profile brief that doesn't mention rates feels incomplete. DeepSeek will naturally weave it in once it's in the prompt.
**How:** one extra row in `SYMBOLS` in `data/market.py`. Zero new dependencies.
**Risk:** negligible.

---

### A1 — Fear & Greed style sentiment indicator `[SHIP]`
**What:** A score (0–100) + label (Extreme Fear → Extreme Greed) with a visual gradient bar and needle.
- **Sources:** VIX via `^VIX` (60% weight) + S&P 500 10-day momentum (40% weight). Both pulled from yfinance, no new API key.
- **Formula:** `vix_score = clamp(100 − (vix − 10) / 30 × 100, 0, 100)` / `momentum_score = clamp(50 + sp10d_pct × 5, 0, 100)`
- **Labels:** 0–20 Extreme Fear, 21–40 Fear, 41–60 Neutral, 61–80 Greed, 81–100 Extreme Greed
- **Visual:** horizontal gradient bar (red → amber → green), dark needle at computed position, scale labels below, `ⓘ` info button that explains methodology on hover/focus.
- **Placement:** inside the Snapshot panel, below the market grid.
**Why it's good in a demo:** one glanceable "mood of the market" signal. Easy to narrate: "I added a live sentiment read so the RM can frame the brief before the client even asks."
**Risk:** low — yfinance only, no new env var, falls back gracefully to hidden widget if VIX fetch fails.

---

### A2 — SGD interest rate / SOR or overnight rate `[MAYBE]`
~~**What:** Singapore Overnight Rate Average (SORA) or 3-month SGD SIBOR proxy, via yfinance (`^SBOR`?) or a static daily value from MAS public data.~~
~~**Why:** relevant for Singapore-centric / Fixed Income profiles; makes the brief feel more Singapore-specific.~~
~~**Risk:** yfinance coverage of SORA is patchy; MAS data scraping adds complexity. Probably skip unless it just works with a quick test.~~
> **Status:** Deprioritised — yfinance SORA coverage unreliable. Revisit only if A3 10Y yield is not sufficient for rates framing.

---

### A4 — Singapore property index / S-REIT proxy `[MAYBE]`
**What:** Mapletree Pan Asia Commercial Trust (`N2IU.SI`) or iShares Asia Property ETF as a REIT proxy, via yfinance.
**Why:** relevant for Real Assets profile; makes the Singapore asset class feel real.
**Risk:** single stock/ETF as a proxy is defensible but not a "property index." Mention it as what it is.

---

### A5 — Crypto (Bitcoin) `[SKIP]`
~~**What:** `BTC-USD` via yfinance.~~
~~**Why skip:** OCBC bank context — Bitcoin on a wealth brief for a bank interview is tonally off unless specifically requested. Not worth the risk.~~

---

### A6 — Economic calendar / upcoming events `[SKIP]`
~~**What:** Fed meeting dates, SGX earnings, MAS policy dates. No free real-time API without significant effort.~~
~~**Why skip:** requires a paid calendar API or manual hardcoding. Too much for the time budget.~~

---

## B. UI / UX polish

> **Status (2026-07-18):** All UI polish items on hold — not clear how/where to place them. Revisit after demo experience.

### B1 — Market cell colour + sparkline `[HOLD]`
~~**What:** Each snap-cell background gets a very subtle red/green tint (5% opacity) based on direction. Optional: tiny 5-day sparkline SVG drawn inline from yfinance history already being fetched.~~
~~**How (tint only — 30 min):** add `data-arrow="↑"` attribute in template → CSS `[data-arrow="↑"] { background: rgba(22,163,74,0.06); }`. Zero JS.~~
~~**How (sparkline — 1.5h):** pass `history_points` (list of 5 closes) per series → render as inline `<svg>` with a polyline. Requires template change + passing extra data from `market.py`.~~

---

### B2 — "Refresh market data" button `[HOLD]`
~~**What:** A small "Refresh ↺" link next to the snapshot timestamp that calls `GET /market` via HTMX and updates just the snapshot grid, without reloading the brief.~~
~~**Why:** shows the HTMX architecture working live. Good demo talking point: "snapshot and brief are decoupled — refresh data without losing the persona."~~

---

### B3 — Persona quick-select chips `[HOLD]`
~~**What:** Above the form, 3–4 pre-set persona buttons ("Conservative HNW Singapore", "Growth-oriented Mass Affluent Global") that pre-fill the form fields and immediately trigger a generate.~~
~~**Why:** removes the 30-second form-fill for demo flow. The interviewer sees the persona switching instantly.~~

---

### B4 — Side-by-side persona comparison `[HOLD]`
~~**What:** Generate two briefs simultaneously (same snapshot, two profiles) and show them in a 2-column layout.~~
~~**Why:** the whole demo point is "same data, different framing" — showing them side-by-side makes that viscerally obvious.~~
~~**Risk:** doubles DeepSeek calls per comparison; layout is complex on mobile. Medium-high effort.~~

---

### B5 — Brief section timestamp + "Last generated" `[SKIP]`
~~Small QoL. Not worth the time.~~

---

### B6 — Skeleton loader instead of plain spinner `[MAYBE]`
**What:** Grey animated placeholder blocks (CSS only, no JS) while the brief loads, instead of a spinner + text.
**Why:** looks much more polished — feels like a real banking app. Pure CSS.
**Risk:** low-medium; needs careful z-index and reveal behaviour with HTMX swap.

---

### B7 — Dark/light mode toggle `[SKIP]`
~~Not relevant to the demo story. Don't add noise.~~

---

## C. LLM / brief quality

### C1 — "Key action for today" callout sentence `[MAYBE]`
**What:** The brief already ends with a risk/opportunity sentence (from the system prompt). Add a styled callout box that highlights just that final sentence — visually separated from the paragraphs.
**Why:** gives the RM something they can literally read aloud to a client. Interviewers see "AI → actionable output" in 3 seconds.
**How:** ask DeepSeek to end with a clearly marked action line (e.g. "Action signal: …") and parse that prefix. Medium effort, high demo value.

---

### C2 — Prompt version / model displayed on brief `[MAYBE]`
Small credibility signal. Low effort. Could help if someone asks "how does this work".

---

## D. RM contact buttons `[SHIP]`

**What:** Two large, prominent CTA buttons below the brief — "📞 Call your RM" and "✉ Message your RM".
**Why:** closes the loop on the demo story: brief informs the RM → RM contacts the client. One-click action. Also makes the app feel like a real product, not a prototype.
**How:** inside `partials/brief.html`, after the brief text. `href="tel:+6565381111"` and `href="sms:+6565381111"` (placeholder OCBC number — swap for real in prod). OCBC brand-red call button, ghost variant for message button.
**Risk:** negligible.

---

## Shipping order (current session)

| # | Item | Est. time |
|---|---|---|
| 1 | A3: 10Y Treasury in SYMBOLS | 15 min |
| 2 | A1: `compute_sentiment()` + visual bar + ⓘ tooltip | 60 min |
| 3 | D: RM contact buttons in brief partial | 20 min |
| 4 | Page reorder (Brief first) | 10 min |
| 5 | CSS: sentiment bar + RM buttons | 30 min |

---

## Open questions — resolved

- ~~Do you want to reorder sections?~~ **Yes — Brief first.**
- ~~Pre-select a default persona?~~ Not yet — keep V1 (no profile) as default for auto-load.
- ~~Sparkline?~~ On hold.
