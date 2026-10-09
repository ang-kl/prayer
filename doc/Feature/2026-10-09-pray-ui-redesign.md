---
flow: spec
title: "Friendly, reverent Pray screen with a one-sentence path (Lamp Path)"
act: "directive"
force: "MUST"
scope:
  - "doc/Feature/2026-10-09-pray-ui-redesign.md"
  - "theme.js"
  - "styles.css"
  - "experience.css"
  - "experience.js"
  - "journey-ui.js"
  - "index.html"
  - "app.js"
  - "teaching.js"        # layout wrapper only (A12)
  - "guidance-core.js"   # quick-prayer wording only (A15)
  - "README.md"
  - "tests/simple-path.test.cjs"
  - "tests/simple-path-browser.py"
  - "tests/scroll-stability-browser.py"   # Amendment 2
  - ".github/workflows/preview-check.yml"   # manual-dispatch steps for the new checks (A16)
verify: ""
---

# Friendly, reverent Pray screen with a one-sentence path

Version 1.0 for approval · 09-10 '26 · from a read-only discovery run (5 readers, 3 directions, 3 judges, 1 critic) and the owner's answers of 09-10 '26 07:37 and 07:45 SGT.

## Intent
Brief in TIOAMC + Close order:
- **Task:** Redesign the UI so it is friendly for people who give only the first input, while others can explain each W.H.E.M.S. area in detail.
- **Invariants:** The goal of the W.H.E.M.S. web app does not change (see the Invariants table).
- **Output:** A revamped Pray screen with a professional, reverent Christian look and feel. The other routes inherit the new look only (A6).
- **Assumptions:** The audience runs from new believers to seniors of about 70, including people whose first language is not English (see the Assumptions table).
- **Material:** `doc/background.MD`, `README.md`, the current code and tests on `main` at `5d8c0ee`, and the discovery results of 09-10 '26.
- **Context (confirmed by the owner):** Wholehearted helps a person bring a real situation before God truthfully and respond faithfully, without the app deciding for them. Many intended users are older, newer to faith or reading in a second language. Today they meet about 1,000 words and 56 controls before the prayer buttons, and the issue box sits 1.7 to 3.3 screens down on a phone. They need a calm, legible page where one honest sentence is enough, and where going deeper stays an invitation rather than a demand.
- **Close:** Done when the acceptance criteria pass on the agreed phone matrix in portrait and landscape and the existing test contract still passes unchanged. Hardest invariant: the quick path never ticks AI consent or the understanding acknowledgement, and never sends anything.

- Outcome: one large "Pray with what I have written" button directly under the issue box makes all three prayers on the device. A clearly optional "Go deeper in each area" route keeps the five areas open in the page.
- Force: MUST (the owner wrote "redesign is necessary", 09-10 '26 00:10 SGT).
- Done when: every acceptance criterion below passes and an INVARIANTS REPORT is given.

## Interpretation
- UNDERSTANDING: Redesign the Pray route along the Lamp Path direction (judges' total 23.5, against Vellum 18.5 and Calm Modern 17), with the judges' grafts. The look is book-like and calm (parchment, deep ink, one deep purple for the main action, thin gilt hairlines, system book fonts) inside today's CSP. The data model, journal schema and every existing test stay unchanged.
- GAPS: none. Q1 to Q6 were answered "a", the Context was confirmed, and A2, A6, A7, A10, A11, A14 and A16 were confirmed on 09-10 '26.

## Assumptions
| ID | Assumption | Status | Note |
|----|------------|--------|------|
| A1 | "The first-time input" is the issue box, written fresh on each visit; it is not a set-up remembered across visits | confirmed | Q1a |
| A2 | "Explain detailing inputs" means the person's own words in each open reply box; the area help text may sit one tap away in "Help with this question" | confirmed | 07:45 SGT |
| A3 | The quick path is the existing local branch with a second entry point; it never ticks consent or the acknowledgement and sends nothing | confirmed | Q1a |
| A4 | All five areas stay open with visible reply boxes, so no existing test is edited | confirmed | Q1a |
| A5 | A one-tap path keeps the goal, because the five areas stay visible between the issue and the prayers | confirmed | Q1a |
| A6 | Only the Pray route is restructured; Journal, Browse, Entry, Download, Scripture and the dialogs inherit tokens and type scale only | confirmed | 07:45 SGT |
| A7 | System fonts only; vercel.json is unchanged | confirmed | 07:45 SGT |
| A8 | Look: parchment, deep ink, one deep purple for the single main action, thin gilt hairlines, and an empty Latin cross (inline SVG) replacing the "w." monogram. No colour carries a religious meaning, no cross or gilt sits on AI-written text, at most 3 accent uses per screen. Owner reviews screenshots at the first checkpoint | confirmed | Q3a |
| A9 | English-only interface rewritten in plain English (about CEFR B1); locked and test-pinned wording stays verbatim; `lang="en-GB"`; the brand and the W.H.E.M.S. letters are protected from browser translation; typed Chinese, Malay or Tamil displays correctly | confirmed | Q4a |
| A10 | No new persistence; app.js keeps exactly one localStorage.setItem and "Nothing is saved automatically" stays true | confirmed | 07:45 SGT |
| A11 | The build stays 0.0.005 and native confirm() is kept | confirmed | 07:45 SGT |
| A12 | The teaching intro's two example prayers go into a closed "Show two short example prayers" fold, with text unchanged | confirmed | Q6a |
| A13 | Proof: Chromium matrix here; WebKit in CI by manual dispatch on a pushed branch (needs the owner's ALLOW); then the owner's 10-step check on their own iPhone and Android in both orientations; anything unchecked is reported Not Verifiable | confirmed | Q5a |
| A14 | The five core questions keep today's on-screen wording (journey-ui.js:7); their four differing versions are recorded, not resolved | confirmed | 07:45 SGT |
| A15 | A static "When to get other help as well" list from background.MD section 23 sits near the issue box, and the quick prayers mention the issue grammatically | confirmed | Q6a |
| A16 | preview-check.yml gains steps that run the new phone checks in Chromium and WebKit on manual dispatch | confirmed | 07:45 SGT |
| A17 | "Friendly" means the Q2a numbers: issue box on the first screen of 360 to 440 wide portrait phones (at most 1.1 screens at 320x568) and, in landscape, issue box and main button both on the first screen; one field and one tap to pray, one more tap to Save; exactly one primary button per screen; no pop-up dialog on the quick path; body text 20px, nothing under 18px; helper-text contrast at least 7:1; every control at least 48px; the visible line "Your words stay only on this page until you tap Save." | confirmed | Q2a |

## Invariants
| ID | Maxim | Scope | Limit | Contrary | Check |
|----|-------|-------|-------|----------|-------|
| I1 | The app goal does not change: describe, optionally reflect through five areas, consider the next step, pray in three forms, save explicitly | Pray route, save flow | Presentation and copy may change; data model and schema may not | A skip path that turns the scaffold into a one-shot generator | completion-browser.py (unchanged) + simple-path-browser.py quick_path_keeps_whems_in_dom |
| I2 | The issue is the only input needed for local prayers | quick and local buttons | AI also needs consent; AI prayers after a reflection also need the acknowledgement | New required fields | simple-path-browser.py quick_issue_only, quick_blank_issue |
| I3 | AI stays opt-in: consent defaults off, its sentence is verbatim, nothing is sent without an AI button press | consent box, quick path, typing, rotation | /api/guidance only | Shortcuts that pre-tick or send | about-introduction.test.cjs:16 + simple-path-browser.py quick_sends_nothing |
| I4 | The understanding acknowledgement is never ticked automatically, and editing resets it | journey-ui.js:88, :108-110, :129 | Only after an AI reflection | Pre-confirming to save a tap | experience-browser.py:127-143; inplace-browser.py:134-137 |
| I5 | All five areas render open with a visible reply box | journey-ui.js area markup | Help text may sit in a details that is not class "area" | Collapsing areas | guidance.test.cjs:35 + simple-path.test.cjs areas_open_count |
| I6 | No score, progress meter, badge or "x of 5" count | all new markup and copy | Buttons may name the next area | Gamified progress | simple-path.test.cjs no_progress_markup |
| I7 | Saving stays explicit and local; no new storage key | app.js, theme.js, journey-ui.js, experience.js | Existing journal key only | Convenience persistence | design-export.test.cjs:15 + simple-path.test.cjs no_new_storage |
| I8 | Generation and navigation update the page in place | journey-ui.js | Route changes may render | Re-render or scroll-to-top | prayer-output.test.cjs:36; inplace-browser.py:128-149 |
| I9 | The production CSP holds: system fonts, no inline styles, SVG presentation attributes only | index.html, all browser JS and CSS | export.js keeps its own style under its own CSP | Web fonts or inline styles | simple-path.test.cjs csp_hygiene + simple-path-browser.py csp_zero_violations + `git diff --quiet origin/main -- vercel.json` |
| I10 | Locked files stay byte-identical | about.js, api/scripture.js, core.js, journal.js, catalogue.js, LICENSE | none | Rewording locked copy | about-introduction.test.cjs:14-15 |
| I11 | No existing test file is edited, and the contract passes | tests/ | New files listed in scope | Editing tests to pass (F7) | `node build.cjs && npm test` 150/150 + the three browser suites + `git diff --name-only --diff-filter=M origin/main -- tests/` empty |
| I12 | Accessibility floors hold: contrast, 48px controls, 18px text floor, no overflow across the matrix and at 200% | tokens, styles, all phone sizes | Inline links in sentences exempt | Dense layouts | experience.test.cjs:12-16 + simple-path-browser.py matrix_no_overflow, tap_targets, min_font + simple-path.test.cjs tokens_contrast |
| I13 | Thanksgiving and request stay independent and visible in each area | area markup; app.js:97 | Notes appear only when chosen | Merging choices | completion-browser.py thank and ask steps |
| I14 | Scripture stays separate: no quoted verse text in the UI | journey-ui.js, index.html | Catalogue context lines stay | Decorative verse banners | simple-path.test.cjs no_quoted_scripture |
| I15 | The human chooses the next step; the principle lines stay verbatim | #guide-decision | Surrounding labels may be simplified | Softening human responsibility | simple-path.test.cjs verbatim_invariant_lines |
| I16 | No new browser asset file | build.cjs | Test files are not assets | Splitting files, forcing F7 | `git diff --quiet origin/main -- build.cjs`; build prints 16 assets |
| I17 | The local prayer contract holds: the extended prayer contains the issue, the W.H.E.M.S. form keeps all five headings, length 450 to 900 words, community voice and no judgement wording | guidance-core.js local() | The sentence and W.H.E.M.S. wording may change (A15) | A wording fix that breaks the existing local tests | guidance.test.cjs:12, :16, :24 (unchanged) + simple-path.test.cjs quick_prayer_wording |
| I18 | Restraint in the look: no cross or gilt inside prayer or AI containers, no colour named with a religious meaning, accent used sparingly | all new markup, CSS and copy | The brand mark in the header | Ornament on AI text; symbolic colour claims | simple-path.test.cjs look_rules + owner screenshot review (A8) |

## Acceptance criteria
- [ ] First screen: at Standard size the issue box top is within the first screen on every portrait phone 360 to 440 wide, at most 1.1 screens at 320x568; in every landscape size the issue box and the main button are both on the first screen → simple-path-browser.py first_screen
- [ ] Quick path: issue only plus one tap gives three non-empty prayers, 0 /api/guidance requests, 0 storage writes, no dialog event, focus in the prayers, and the status says "Nothing was sent" → quick_issue_only
- [ ] Empty issue plus the quick button shows feedback, sets aria-invalid, focuses the issue box and sends nothing → quick_blank_issue
- [ ] Two taps within 800ms fill the prayers once and raise no dialog → quick_double_tap
- [ ] "Go to Save" after the quick path focuses Save (one more tap to save) → go_to_save
- [ ] AI path: consent, then AI prayers, sends exactly one request; no summary gate without a reflection; the AI state line shows consent → ai_quick_path
- [ ] Deep path: "Go deeper in each area" and each "Next: <Area>" focus the next area; all five reply boxes stay visible → deep_path_navigation
- [ ] Exactly one primary-styled button is visible in any one screen-height, sampled every half screen at 390x844 and 375x667 → one_primary_per_screen
- [ ] "Your words stay only on this page until you tap Save." is visible near the issue box → save_promise_line
- [ ] The "When to get other help as well" list is present near the issue box, static, with no network request → safety_list
- [ ] No horizontal overflow at any matrix size and text size; the nav and dock wrap at 390x844 with 200% text → matrix_no_overflow + existing overflow checks
- [ ] Every visible control is at least 48x48 and the main action at least 56px tall → tap_targets
- [ ] At Standard size body text is 20px and no visible text is under 18px; form controls are at least 18px at every size → min_font
- [ ] Token contrast: ink and helper text at least 7:1 on every surface; accents at least 4.5:1; lines at least 3:1 → simple-path.test.cjs tokens_contrast
- [ ] Rotation while typing keeps the text and focus, sends nothing and causes no overflow; the dock never covers the content column in landscape → rotation
- [ ] Simulated insets (59px sides, 34px bottom) are cleared by header, main, footer, reader and dock in both orientations → simulated_safe_area
- [ ] With an 844x170 landscape keyboard, the focused field's label and caret line stay visible → landscape_keyboard
- [ ] Zero CSP violations across the paths, routes and dialogs when served with the vercel.json headers → csp_zero_violations
- [ ] Forced-colours mode shows the current nav item and the chosen text size → forced_colors
- [ ] `<html lang="en-GB">`; the brand and the W.H.E.M.S. letters carry `translate="no"`; typed Chinese, Malay and Tamil text round-trips in the issue box → simple-path.test.cjs language_rules + simple-path-browser.py typed_scripts
- [ ] Quick prayers mention the issue grammatically in the sentence and the W.H.E.M.S. form, for a question-shaped issue too → simple-path.test.cjs quick_prayer_wording
- [ ] The brand mark is an empty Latin cross in inline SVG; the "w." monogram is gone → simple-path.test.cjs look_rules
- [ ] The existing contract passes unchanged: 150 node tests and the completion, experience and inplace suites in http and dom modes on Chromium; WebKit by manual CI dispatch → `node build.cjs && npm test`; browser suites; preview-check.yml dispatch

## Device matrix
Portrait: 320x568, 360x740, 360x800, 375x667, 375x812, 390x844, 393x852, 402x874, 412x915, 430x932, 440x956, each also in landscape. Tablets 768x1024 and 1024x768 for regression. Text sizes: Standard, Larger, Largest, plus 200% root. Keyboards: 390x340 portrait and 844x170 landscape. Engines: Chromium here; WebKit by CI manual dispatch (needs ALLOW push). Real phones: the owner's 10-step checklist; otherwise Not Verifiable.

## Out of scope
- vercel.json or CSP changes, and web fonts
- Editing byte-locked files; resolving the four-way core-question wording conflict (A14)
- Structural redesign of Journal, Browse, Entry, Download, Scripture and the dialogs (A6)
- Dark mode, a translated interface, right-to-left layout, new persistence, a version bump, replacing confirm(), an offline app

## Evidence
Filled at the end: INVARIANTS REPORT, verify output, browser-suite results, screenshots per matrix size, PR link.
Editing this file after approval voids the approval; append amendments and ask for APPROVE again.

## Amendment 1 · 09-10 '26
Appended after the approval of 08:08 SGT, from the owner's iPhone Safari screenshots and answers given between 10:18 and 10:24 SGT. Everything above stays in force except where this amendment corrects it.

Evidence (Chromium on the live build `5d8c0ee`, at the owner's phone size 430x932):
- The header is 143px, 15% of the screen.
- The floating bar is 310x48px, 72% of the width.
- Body line spacing is 1.65.
- Only 48% of the first-screen rows below the header hold text or controls.
- The issue box is 1.73 screens down.
- Typing jump reproduced with the existing keyboard model: the page moves 60px down and back up on every keystroke, because the app re-scrolls to clear the floating bar (experience.js:43, :61, bar at experience.css:64) while the browser keeps the caret visible.

| ID | Assumption | Status | Note |
|----|------------|--------|------|
| A18 | Floating bar: hidden while the keyboard is open (H1); appears only after scrolling more than two screens down (H2); on phones (narrower than 700px) a single 48px Contents button with no Up/Down (H3); wider screens keep Contents, Up and Down | confirmed | owner, 10:18-10:24 SGT |
| A19 | The typing-jump fix ships with this redesign; there is no separate hotfix, so the jump stays on the live site until release | confirmed | owner, 10:18-10:24 SGT |
| A20 | "Less white space" means Denser: header at most 72px on phones 360px wide and up (at most 112px at 320); at least 85% of the first-screen rows below the header hold text or controls; body line spacing 1.45; body text stays 20px | confirmed | owner, 10:18-10:24 SGT |
| A21 | Correction to A17 for the header only: row 1 is the logo and title as a 32px-tall link; row 2 holds the Pray, Journal and Scripture tabs and the Aa button at 40px. Every other control stays at least 48px | corrected | owner's choice, 10:18-10:24 SGT; all three still meet WCAG 2.5.8 (24px minimum) |
| A22 | The existing test lines tests/experience-browser.py:176-177, :213, :215 and :232 may change only as far as A18 requires. That file is outside the scope list, so each edit raises the owner's F3 and F7 confirmation | confirmed | owner, 10:18-10:24 SGT |

| ID | Maxim | Scope | Limit | Contrary | Check |
|----|-------|-------|-------|----------|-------|
| I19 | While the keyboard is open, the app never scrolls the page in answer to typing or to the browser's own panning | experience.js | One adjustment after a focus or a real viewport resize, once the viewport has settled | The app and the browser fighting over the scroll position, which makes the screen jump | simple-path-browser.py typing_no_jump |
| I20 | The floating bar never sits where the browser keeps the caret | experience.js, experience.css | Wider screens keep Up and Down when no field is focused | The bar covering the text being typed | simple-path-browser.py bar_hidden_while_typing |

Acceptance criteria added (the A21 exceptions apply to tap_targets):
- [ ] Typing: with the keyboard model open and the caret at the end of a long reply, ten cycles of "browser brings the caret into view, then one keystroke" cause no window scroll by the app → simple-path-browser.py typing_no_jump
- [ ] The bar is hidden while the keyboard is open and is back within 300ms after it closes → bar_hidden_while_typing
- [ ] The bar is absent while scrollY is at most 2 x innerHeight and present beyond that → bar_after_two_screens
- [ ] Below 700px wide the bar is one 48x48 Contents button with no Up/Down; at 768 and wider Contents, Up and Down remain → bar_phone_single_button
- [ ] The header is at most 72px tall at Standard size on every portrait phone 360px wide and up, and at most 112px at 320. The logo link is at least 32px tall, the tabs and Aa at least 40px, and every other control at least 48px → header_height + tap_targets
- [ ] At least 85% of the first-screen rows below the header hold text or controls at 430x932, 393x852 and 375x667. Measured as the union of pixel rows covered by leaf elements that contain text or are form controls, from the header's bottom edge to the viewport's bottom edge → first_screen_density
- [ ] Body line spacing is 1.45 (±0.02) with 20px body text → line_spacing

## Amendment 2 · 09-10 '26 · scroll stability and the floating button
Appended after the release of `7741471` (Production, 14:02 SGT), from the owner's report at 14:13 SGT that the live page still jumps up and down, and their answers at 14:16 SGT. Everything above stays in force except where this amendment corrects it.

Owner's observations: the page jumps while scrolling with a finger, when tapping into a box, and while typing (iPhone Safari). Density stays as released. The floating button should be smaller, hidden at the top and at the bottom, and hidden while the finger is scrolling.

Causes found in the released code (evidence is file:line; the iOS behaviour is inference from documented Safari viewport behaviour, not reproduced here, since no iOS device is available):
- C1 Reply boxes and prayer boxes are capped with `dvh` and grow with their content (`experience.css:62` `max-height:50dvh` and `:86` `max-height:min(36rem,65dvh)`, both with `field-sizing:content`; `field-sizing` is new in this redesign, `5d8c0ee` had fixed rows). On iOS Safari `dvh` changes as the toolbars collapse and expand during a finger scroll, so every box at its cap changes height while the page scrolls, which moves everything below it: the scroll jump.
- C2 Tapping a box triggers two app scrolls during Safari's own keyboard animation: `experience.js:184` (120ms after focus) and `:48` (150ms after each viewport resize, re-armed by every intermediate keyboard height): the tap jump.
- C3 `resized` at `experience.js:29-30` counts a height change as a resize. On iOS `innerHeight` changes whenever the toolbars collapse while Safari pans to follow the caret, so typing re-triggers the `:48` adjustment: the typing jump.
- C4 The Contents button is 132x48 with a word, and it toggles at exactly two screens (`experience.js:36`), so it flickers around that boundary and competes with the content.

| ID | Assumption | Status | Note |
|----|------------|--------|------|
| A23 | In-flow elements are never sized with `dvh`, `vh`, `svh` fractions that change during a scroll, or `--vp-height`; boxes are capped in rem (reply 24rem, prayers 36rem) and keep `field-sizing:content` | confirmed | owner, 14:16 SGT ("while scrolling") |
| A24 | The app scrolls at most once per keyboard opening, 400ms after the last viewport change, and only when the focused box or its label is more than 24px outside the visible area; it never scrolls on focus alone, on typing, or on a height-only viewport change | confirmed | owner, 14:16 SGT ("tap", "type") |
| A25 | On phones the floating button is one round 48x48 icon button with an accessible name and no visible word; it is hidden within two screens of the top (unchanged), within one screen of the end, and while the page is being scrolled, returning within 100ms after the scroll stops | confirmed | owner, 14:16 SGT |
| A26 | Density stays as released (A20) | confirmed | owner, 14:16 SGT |
| A27 | New checks go in a new file `tests/scroll-stability-browser.py`; no existing test file changes | confirmed | keeps F7 out of this amendment |

| ID | Maxim | Scope | Limit | Contrary | Check |
|----|-------|-------|-------|----------|-------|
| I21 | Nothing in the page flow changes size because the viewport height changed | styles.css, experience.css | Fixed overlays (reader, notice, bar) may use viewport units | Boxes that breathe with the toolbars and shake the page | scroll-stability-browser.py toolbar_no_shift + static scan no_dynamic_units |
| I22 | The app never fights the browser for the scroll position: one adjustment per keyboard opening at most, after it settles | experience.js | The owner's own navigation (Go deeper, Next, Go to Save, Contents) may scroll once | Timers that scroll during Safari's animations | scroll-stability-browser.py tap_no_jump, typing_no_jump (existing) |
| I23 | The floating button never competes with reading or typing | experience.js, experience.css | Wider screens keep Contents, Up and Down past two screens | A bar that shows at the ends or while scrolling | scroll-stability-browser.py fab_round, fab_hidden_near_end, fab_hidden_while_scrolling + existing bar checks |

Acceptance criteria added:
- [ ] No in-flow element uses `dvh`, `vh`, `svh` or `var(--vp-height)` in its sizing; the reader, the notice and the bar may → no_dynamic_units
- [ ] With a focused reply box and `innerHeight` shrinking by 60px in three steps (toolbar model), no textarea changes height and the app makes no scroll → toolbar_no_shift
- [ ] Tapping a box, then a five-step keyboard animation over 250ms: the app makes at most one scroll, no earlier than 400ms after the last step, and none when the box is already within view → tap_no_jump
- [ ] On phones the bar is a single 48x48 button with no visible text and an aria-label; its width equals its height → fab_round
- [ ] The bar is hidden when scrollY is within one screen of the end, and at the very end → fab_hidden_near_end
- [ ] During a burst of scroll events the bar is hidden; it is visible 100ms after the last one (and within the existing checks' 160ms) → fab_hidden_while_scrolling
- [ ] The existing suites pass unchanged: 163 node tests, simple-path-browser.py 29/29, the three existing browser suites; preview-check.yml also runs the new file on manual dispatch (A16)

Scope addition for this amendment: `tests/scroll-stability-browser.py` (new). The scope list above already covers experience.js, experience.css, styles.css and preview-check.yml.
