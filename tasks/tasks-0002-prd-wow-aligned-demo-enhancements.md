# Tasks: WoW-Aligned Demo Enhancements

**PRD:** `tasks/0002-prd-wow-aligned-demo-enhancements.md`  
**Depends on:** `tasks/0001-prd-wealth-market-brief-generator.md` (complete)  
**Status:** Ready for implementation

## Relevant Files

- `wealth-brief/llm/brief.py` — Extend prompts for structured blocks (`BRIEF` / `INVESTMENT_IDEAS` / `WATCH` / `HOUSE_VIEW`); add parser + email boilerplate helper; optional `portfolio_mix` in V2 prompt.
- `wealth-brief/main.py` — Pass new form field(s) into `generate_brief`; pass parsed panels into brief partial context.
- `wealth-brief/templates/index.html` — Persona chips above profile form; optional portfolio mix input; page footer disclaimer.
- `wealth-brief/templates/partials/brief.html` — Render ideas / watch / house-view panels + draft email block + copy control (demo labels only).
- `wealth-brief/static/app.js` — Chip prefill (no auto-submit); copy email draft; keep asset max-2 + Generate explicit.
- `wealth-brief/static/style.css` — Chip, panel, email draft, footer styles (OCBC red/white).
- `wealth-brief/README.md` — Link PRD 0002; V3 research-ingestion path; copy-audit note (no official OCBC claims).
- `wealth-brief/tests/test_brief.py` — Structured parse happy path + missing-block soft-fail; portfolio mix in prompt; email template.
- `wealth-brief/tests/test_routes.py` — `/` footer; `/generate` returns new panels when mocked ok; soft-fail when LLM fails.
- `tasks/0002-prd-wow-aligned-demo-enhancements.md` — Source of truth for FR-20–39.

### Notes

- Prefer `pytest` from `wealth-brief/` (not Jest). Red/green TDD for production code under `wealth-brief/`.
- Do **not** re-fetch yfinance on `POST /generate` (PRD 0001 FR-12).
- One DeepSeek call returns structured plain-text blocks; email wraps `BRIEF` only — no second free-form email LLM call.
- UI must never claim official OCBC recommendations/advice; use “demo” / “simulated” labelling.
- Map chip presets to **existing** form `value=` strings (e.g. `Fixed Income / Bonds`, `Legacy / Estate Planning`) — do not invent mismatched option values.
- V3 ingestion pipeline is **document + optional stub only** unless product owner expands scope.
- Junior build order: 1.0 → 2.0 → 3.0 → 4.0 → 5.0 → 6.0 → 7.0 → 8.0.

## Tasks

- [x] 1.0 Persona quick-select chips (FR-20–22)
  - [x] 1.1 Add a chip row above `#client-profile` in `index.html` with 4 buttons (type=`button`, not submit): Conservative HNW · Singapore; Income · Affluent · Asia; Growth · HNW · Global; Legacy · UHNW · Singapore
  - [x] 1.2 In `app.js`, on chip click: select matching `tier` / `goal` / `geography` radios; clear then check ≤2 `asset_classes` using existing checkbox values; call existing `syncAssetLimit()`; highlight active chip; **do not** call `/generate`
  - [x] 1.3 Confirm user can edit any field after a chip click and must press **Generate My Brief** to submit (FR-21–22)
  - [x] 1.4 Style chips in `style.css` as secondary/outline controls; active state clear; do not compete visually with the primary Generate CTA
  - [x] 1.5 Manual check: each chip fills a valid, submittable form without validation errors

- [x] 2.0 Structured one-call LLM output + Investment ideas panel (FR-23–25, FR-37)
  - [x] 2.1 RED: add `tests/test_brief.py` cases for parsing a labelled multi-block response (`BRIEF`, `INVESTMENT_IDEAS`, `WATCH`, `HOUSE_VIEW`) and for missing blocks soft-fail
  - [x] 2.2 Implement `parse_structured_brief_response()` (or equivalent) in `llm/brief.py` returning `{ paragraphs, ideas, watch, house_view }` with empty lists when markers absent
  - [x] 2.3 Update system/user prompts so DeepSeek returns the labelled plain-text contract (no markdown); keep V1/V2 persona guidance; never invent prices/news not in the payload
  - [x] 2.4 Update `generate_brief()` to return structured fields + existing `{ ok, text, badge }`; on LLM failure keep safe user message and empty panels (FR-39)
  - [x] 2.5 Wire `main.py` `/generate` to pass `ideas` into the brief partial; render **Investment ideas (demo)** with 2–3 bullets when `ok` and ideas present; hide when empty/failed (FR-23–25)
  - [x] 2.6 GREEN: run `pytest tests/test_brief.py` then extend `test_routes.py` mock so `/generate` HTML includes the demo ideas heading when mocked structured content is returned

- [x] 3.0 Draft client email from fixed boilerplate + brief (FR-26–28)
  - [x] 3.1 RED: unit test that `build_client_email(brief_text)` wraps paragraphs in the PRD canonical template with `[CLIENT_NAME]` and `[RM_NAME]` placeholders (exact boilerplate)
  - [x] 3.2 Implement `build_client_email()` in `llm/brief.py` (or small helper module); use parsed BRIEF text only — no second LLM call
  - [x] 3.3 In `brief.html`, when `ok`, show Draft email block (preformatted) + Copy button + one-line “Template for demo only — not an official OCBC communication.”
  - [x] 3.4 In `app.js`, wire copy for the email draft (reuse/extend existing clipboard helper); do not break brief copy if still present
  - [x] 3.5 GREEN: route/partial test asserts email placeholders and demo disclaimer string appear on successful generate

- [x] 4.0 What to watch today panel (FR-29–30)
  - [x] 4.1 Ensure prompt asks for exactly 3 short WATCH lines (≤ ~12 words); parser yields up to 3 items
  - [x] 4.2 Render **What to watch today** in `brief.html` when `ok` and 3 items exist; hide or show soft fallback if fewer/missing (do not crash)
  - [x] 4.3 Document in code comment (and later README in 8.0) that default is one structured call; separate WATCH call is fallback only if quality is poor
  - [x] 4.4 Extend tests: happy path with 3 watch items; missing WATCH block does not fail the whole brief

- [ ] 5.0 Persistent footer disclaimer (FR-36, FR-38 start)
  - [x] 5.1 Add site footer on `index.html` stating: demonstration prototype; public market data + AI-generated demo narrative/ideas; **not** official OCBC research/advice/recommendation; production path can restrict generation to approved proprietary research
  - [x] 5.2 Style footer muted/small; always present on `GET /` without a modal
  - [x] 5.3 Grep UI copy for forbidden claims (“OCBC recommends”, “official OCBC view”, etc.) and fix any hits
  - [x] 5.4 Route test: `GET /` response contains key disclaimer phrases

- [ ] 6.0 Optional portfolio mix field (FR-31–33)
  - [ ] 6.1 Add optional text input `portfolio_mix` to the profile form (placeholder e.g. `60% equities / 30% bonds / 10% gold`); empty allowed
  - [ ] 6.2 Accept `portfolio_mix` on `POST /generate`; include in profile dict and system/user prompt when non-empty (FR-32)
  - [ ] 6.3 Extend chip prefill in `app.js` with a sample mix string per preset (editable before Generate) (FR-33)
  - [ ] 6.4 Tests: prompt includes mix when provided; omit when blank; existing no-profile / V1 path unchanged

- [ ] 7.0 Simulated house-view card (FR-34–35)
  - [ ] 7.1 Render card titled e.g. **Simulated research view (demo) — not OCBC official research** when `ok` and house_view bullets exist
  - [ ] 7.2 Soft-fail: if HOUSE_VIEW missing, hide card or show 2–3 static demo bullets labelled as placeholder — never crash
  - [ ] 7.3 CSS: simple section consistent with ideas/watch; not a busy dashboard card
  - [ ] 7.4 Tests cover present bullets + missing-block soft-fail path

- [ ] 8.0 Tests, README V3 path, copy audit, demo smoke (FR-38–39)
  - [ ] 8.1 Full regression: `pytest -q` from `wealth-brief/` green
  - [ ] 8.2 Update `README.md`: link PRD 0002; summarise new panels; document V3 ingestion path (§10 of PRD) and interviewer one-liner; note no official OCBC claims
  - [ ] 8.3 Add a short copy-audit checklist to README (or PR description template): forbidden phrases + required “demo/simulated” labels
  - [ ] 8.4 Optional: add `ResearchSource` stub module returning empty/demo passages (no real corpus) — skip if time-boxed; do not build full pipeline
  - [ ] 8.5 Manual demo narrative 2×: chip → optional edit → Generate → brief + ideas + watch + email copy + footer visible; second chip → Generate again with same snapshot numbers
  - [ ] 8.6 Deploy/smoke on Railway when local DoD met; confirm disclaimer + soft-fail still hold remotely
