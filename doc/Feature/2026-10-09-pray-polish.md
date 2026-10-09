---
flow: spec
title: "Pray screen polish: numbered prayers with links, colours, a suggested title, librarian wording, one classic link per tradition"
act: "directive"
force: "MUST"
scope:
  - "doc/Feature/2026-10-09-pray-polish.md"
  - "journey-ui.js"
  - "theme.js"
  - "styles.css"
  - "experience.css"
  - "app.js"            # the two "AI guidance" phrases a person reads
  - "README.md"
  - "doc/background.MD"   # the phrase "AI guidance" where a person reads it; one line on the classic links
  - "tests/simple-path-browser.py"
  - "tests/simple-path.test.cjs"   # the CONSENT constant (A40)
  - "tests/about-introduction.test.cjs"   # the consent-sentence regex (A40)
verify: ""
---

# Pray screen polish

Version 1.0 for approval · 09-10 '26 18:30 SGT · from the owner's eight asks of 17:58 SGT, the answers of 18:14 SGT, and a two-agent research run on classic prayer collections (18:16 to 18:28 SGT; the sandbox proxy denied every outbound page fetch, so its findings rest on search-index snippets and are marked unverified).

## Intent (TIOAMC + Close)
- **Task:** eight small changes to the Pray screen: (1) a suggested title, (2) numbered prayers with links on the "Your three prayers" card, (3) an up arrow under each prayer back to the issue question, (4) bright blue section titles, (5) red headings for Guardrails and the AI box, (6) a distinct background for every typing box, (7) "AI guidance" replaced by librarian-style wording, (8) "Read classic prayers first" becomes one human-written link per tradition.
- **Invariants:** nothing leaves the device without the consent tick; every prayer stays editable; saved entries and the journal format are unchanged; new colours meet WCAG AA 4.5:1 on the paper and card backgrounds; the existing suites pass with only the listed test edits (A40).
- **Output:** the Pray screen as released at `0c1bbff` with the eight changes, plus one phone check per change in `tests/simple-path-browser.py`.
- **Assumptions:** see the table; A32 to A39 were answered by the owner at 18:14 SGT.
- **Material:** `doc/background.MD`, the live code at `0c1bbff`, the research run's shortlist (CCEL Bayly and Taylor, Church of England topical prayers, bcponline.org 1979 BCP, Henry Law; rejected: 1662 BCP page unlocatable, ACNA 2019 and Valley of Vision copyrighted with no per-prayer pages, Matthew Henry PDFs).
- **Context:** the owner finds the released page repetitive and hard to scan on the phone; the prayers need numbers and a way to move between them and the issue; the page's colours give no hierarchy; "guidance" overstates what AI does.
- **Close:** done when each of the eight items has a named check that passes at 390x844, 320x568 and 844x390, the existing suites pass, and the owner sees the changes on the phone. Hardest invariant: no text is sent anywhere by any of these changes (the classic links open external pages only when tapped).

## Interpretation
UNDERSTANDING: a polish pass, not a restructure. The wider simplification of the page (owner, 15:52 SGT; proposal of 15:58 SGT) is still separate and not in this spec.
GAPS closed by the owner's answers: title source (pre-fill from the issue), wording (librarian in the consent sentence), classic prayers (one link per tradition), Invariants and Close (use mine).

| ID | Assumption | Status | Note |
|----|------------|--------|------|
| A32 | The Save title fills itself from the first eight words of the issue (trailing punctuation dropped, "…" when cut), updates while the issue is typed until the person edits the title, and stays editable; nothing else changes in Save | confirmed | owner, 18:14 SGT |
| A33 | Prayer headings become "1. One-sentence prayer", "2. W.H.E.M.S. prayer", "3. Extended prayer"; the Contents labels keep their words without numbers | confirmed by inference | the heading text still contains the old words, so the existing text checks hold |
| A34 | The "Your three prayers" card shows three jump links (buttons with data-locate, 48px tall, quiet style) directly under its intro line; they use the same reveal as "Change what I wrote" | confirmed by inference | plain `href="#id"` links would fight the hash router, so buttons |
| A35 | Each prayer block ends with one quiet button "↑ Back to what is happening" (48px tall, small text) that reveals `#guidance-issue` | confirmed | owner, 17:58 SGT |
| A36 | New tokens in theme.js: `--title: #1d4ed8` (section titles, 6.2:1 on paper), `--alert: #b3261e` (Guardrails and the AI box headings, 6.1:1), `--field: #eef3fb` (typing boxes, 14.7:1 with ink). All `#main h2` take `--title`; `#guardrails h2` and `#guide-consent h3` take `--alert`; inputs, selects and textareas take `--field` | pending | the owner may name other hex values; the check recomputes contrast |
| A37 | Consent sentence becomes: "I agree to send the current issue and replies to AI for suggestions. Like a librarian, AI suggests; it does not guide." The heading becomes "Ask AI for suggestions (optional)", the status line "AI suggestions are on (you agreed above)." / "AI suggestions are off."; "AI guidance" is replaced wherever a person reads it in the app and README (journey-ui.js, app.js, README.md); element ids, file names and the server prompt keep the word; doc/background.MD keeps its section headings and gains one line recording the wording change (it is a background document, appended rather than rewritten) | confirmed | owner, 18:14 SGT (option 3) |
| A38 | "Read classic prayers first" keeps its panel and headings ("Early Church · Augustine", "Medieval · Anselm", "Puritan tradition · Matthew Henry") with exactly one link each, and adds "Anglican · Church of England topical prayers" linking to https://www.churchofengland.org/prayer-and-worship/topical-prayers (copyrighted, link only). The first three links stay as released. No prayer text is copied into the app | confirmed | owner, 18:14 SGT; the Anglican URL is unverified from the sandbox (A41) |
| A39 | Invariants and Close as written above | confirmed | owner, 18:14 SGT |
| A40 | Test edits pre-approved: tests/simple-path.test.cjs:15 CONSENT constant; tests/about-introduction.test.cjs:16, the regex that matches the consent sentence in journey-ui.js; any line in tests/simple-path-browser.py that quotes the old consent sentence or "AI help is"; no other existing test file changes. Owner's F7 confirmation is given by this approval | pending | |
| A41 | Links cannot be fetched from this sandbox (proxy denies all hosts); the owner opens the new Anglican link once before or after release. The three existing links have been live since `5d8c0ee` | pending | |

| ID | Maxim | Scope | Limit | Contrary | Check |
|----|-------|-------|-------|----------|-------|
| I27 | The three prayers are numbered and reachable from the card, and each leads back to the issue | journey-ui.js | Numbers only in headings and card links | Prayers that a phone user cannot find or return from | prayer_numbers_and_links |
| I28 | Colours carry hierarchy and stay readable | theme.js, styles.css, experience.css | Forced-colours mode keeps the browser's own colours | A blue or red that fails 4.5:1 | heading_and_field_colours |
| I29 | AI is described as a librarian's suggestions, never guidance | journey-ui.js, app.js, README, background.MD | Ids and the server file keep the word | "Guidance" in any sentence a person reads | librarian_wording |
| I30 | The title suggests itself and yields to the person | journey-ui.js | Only while the title is unedited | A suggestion that overwrites a typed title | title_suggestion |
| I31 | Classic prayers: one human-written link per tradition, nothing embedded | journey-ui.js | Linked pages may be copyrighted | Prayer text copied into the app | classic_links |
| I32 | Nothing is sent by any of these changes | journey-ui.js | External pages open only on a tap | A request fired by a link or a title | existing quick_sends_nothing + classic_links (no request on open) |

## Acceptance criteria (each at 390x844, 320x568 and 844x390 unless stated)
- [ ] After the quick tap, the three prayer headings read "1. One-sentence prayer", "2. W.H.E.M.S. prayer", "3. Extended prayer"; the card holds three jump controls whose words match; tapping the third brings `#prayer-extended` into view; tapping its "↑ Back to what is happening" brings `#guidance-issue` into view → prayer_numbers_and_links
- [ ] Every `#main h2` computes to `--title`; `#guardrails h2` and `#guide-consent h3` compute to `--alert`; every input, select and textarea in `#main` computes to `--field`; each pair measured against the paper and the card meets 4.5:1 (text) or differs from the card (field); tap_targets, look_rules and one_primary_per_screen still pass → heading_and_field_colours
- [ ] The consent label text is exactly the A37 sentence; the AI box heading and status line read as A37; the visible text of `#main` contains no "guidance" → librarian_wording
- [ ] Typing an issue fills the Save title with its first eight words; typing more updates it; after the person edits the title, further issue typing leaves it alone; the title is empty when the issue is empty → title_suggestion
- [ ] The classic prayers panel shows four tradition headings, each with exactly one https link, Anglican among them; opening the panel makes no network request → classic_links
- [ ] Existing suites pass: node 163 (with the CONSENT constant updated), simple-path, scroll-stability, experience, inplace, completion

## Out of scope
The wider simplification (one choice, background text moved off the page), the per-prayer "Ask AI again" and "simple starting prayer" buttons, dark mode, the About page (locked), the server prompt in `api/guidance.js`.

## Evidence
Filled at the end: INVARIANTS REPORT, verify output, browser-suite results, screenshots, PR link. Editing this file after approval voids the approval; append amendments and ask for APPROVE again.
