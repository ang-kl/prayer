# Wholehearted - build 0.0.005

A W.H.E.M.S. prayer and discernment workspace. Describe a situation, reflect through
Will, Heart, Emotions, Mind and Soul, consider a faithful next step, and keep three
prayer forms together. Scripture is authoritative; guidance and prayers are editable
applications, not messages from God or assessments of salvation.

## Runtime

No npm dependencies. `node build.cjs` publishes 16 browser assets to `public/`.
Vercel runs two small Node functions in `api/`. `release.json` is the display build
source; package version and journal schema have independent purposes.

## Pray

`Pray` starts with one box: write what is happening and what you are trying to decide.
One tap on "Pray with what I have written" makes three prayers on the device, and nothing
is sent anywhere. The five areas (Will, Heart, Emotions, Mind and Soul) are optional, one
short question each, and any of them can be skipped. AI help runs only after the consent
box is ticked; the AI summary and questions can be corrected before they are relied on.
The three prayers (one sentence, W.H.E.M.S. and an extended prayer in an older devotional
style) sit together and can be edited one by one. Saving is explicit and stays in the
browser. The floating Contents button appears after two screens of reading and leaves
while the keyboard is open; the text-size button (Aa) offers Standard, Larger and Largest.

`Journal` starts with a fresh page. Browsing is deliberate and shows titles/metadata,
not prayer excerpts. Local entries preserve revisions, linked follow-ups and three forms.
Created, updated and prayed-at timestamps are distinct. Response status is writer-entered.
Saving is explicit. HTML/text are reading copies; JSON backup/restore preserves data.
No cloud account, shared journal, automated reminder or answer score is included.

## Server configuration

Set these exact, case-sensitive Vercel variable names for Preview:

- `openai_key`: the user's OpenAI API credential, server only.
- `openai_model`: `gpt-5.4-mini`, or another explicitly chosen compatible GPT model.
- `ESV_API_KEY`: optional Crossway credential for direct API text. Not needed for the
  official embedded ESV reader, which is used when the API is absent or unavailable.

The guide reads the configured model with low reasoning effort, never silently upgrades
to another model, and uses strict structured output plus application validation. It only
accepts the current issue/replies after consent, not whole journals or arbitrary fields.
It requests `store:false`. This is not a zero-retention guarantee: provider policies apply.
No request body, API key or model output is logged by application code.

GET `/api/guidance` is a no-charge configuration health response, not a paid model test.
API calls are triggered only by explicit buttons. A running request can be cancelled;
stale results cannot replace a changed issue. Failed responses preserve earlier writing.
Warm-instance request limits are defence in depth, not a distributed/global spending cap.
Before a public production release, review account budgets and add a deployment-level
abuse/rate control appropriate to its audience. Preview protection is kept intact.

## Scripture

All 15 built-in ranges share `catalogue.js`. Ordinary verse buttons open an in-page
reader. If direct ESV API text is unavailable, the fixed Crossway cross-reference embed
is displayed inside the same dialog. No ESV key, AI reconstruction or bundled Bible
corpus is needed for that view. It requires internet and an unblocked ESV.org connection.

The official embed URL is derived from Crossway's own published cross-reference tool:
https://www.esv.org/resources/esv-crossreference-tool/
https://static.esvmedia.org/crossref/crossref.min.js

ESV text remains supplied by Crossway and separate from the GPL application source.
The embedded site receives the public passage request and ordinary browser/network
metadata, not the journal. A no-referrer policy and sandbox separate it from the app.
The exact allowed host is included in Content-Security-Policy. API text is cached only
in memory; prayers and backups do not bundle ESV passage text. STEP, Blue Letter Bible
and Logos remain explicit further-study links; Logos is not an authenticated integration.

The supplied Acts controller informs source discipline only: preserve references and
wording, separate text from interpretation, do not invent missing quotations. It does
not supply a Bible corpus or authorise running an unrelated lesson-generation task.

## Boundaries and preservation

The human soul is not the Holy Spirit. Distress is not automatically sin. Concern is
not automatically control. Prayer and responsible action are not artificial alternatives.
No app verdict replaces the writer's decision, pastoral counsel or appropriate care.
Historical reading links identify the author/period; new extended prayers are never
attributed to a historical author. The twelve supplied origin-poem lines are retained.

Existing schema-3 records are read with new optional journey/prayerForms fields; v2 data
is copied only on explicit Save and retained. Back up before using an older deployment:
older code does not know the added fields. Per-entry limits are 12 AI-guidance rounds and
25 revisions, with an explicit error rather than silently deleting history. Add a linked
follow-up at the limit. Journal capacity remains 100 entries.

## Verification

Run `node build.cjs` then `node --test tests/*.test.cjs` (163 tests, including
`tests/simple-path.test.cjs` for the Pray screen contract: markup, copy, tokens and CSP hygiene).
The browser suites need Playwright 1.57.0 with Chromium. Set `EVIDENCE_DIR` to a folder
outside the repository, because every suite writes screenshots and logs there:
`BROWSER_MODE=http EVIDENCE_DIR=/tmp/evidence python tests/completion-browser.py`, then the
same for `tests/experience-browser.py`, `tests/inplace-browser.py` and
`tests/simple-path-browser.py` (eleven phone sizes in both orientations, the floating bar,
keyboard and safe-area fixtures, tap targets, text sizes and contrast rules for the Pray
screen). `BROWSER_MODE=dom CHROMIUM_PATH=/usr/bin/chromium` injects the built assets and
storage/API fixtures when local navigation is prohibited; it cannot check the CSP.
`TEST_BROWSER=webkit` runs a suite in Linux WebKit, which is not physical Safari; the CI
workflow runs the Pray screen checks in Chromium and WebKit on a manual dispatch only.
The CI workflow uses real local HTTP and native Chromium storage, with **simulated AI**
responses. `LIVE_ESV=1` also verifies the actual Crossway iframe; `tests/live-scripture.cjs`
checks the exact verse IDs for every range. No paid OpenAI requests are made by CI.
These checks are not native Safari/VoiceOver certification or a guarantee of model
pastoral judgement. API/model access on Vercel must still be checked in that environment.
