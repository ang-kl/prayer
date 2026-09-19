# Wholehearted

W.H.E.M.S. Prayer - Will, Heart, Emotions, Mind and Soul.

Preview redesign: **Pray / Journal / Scripture**, with in-page reading panels and a writing-first journal. No old title or prayer is displayed on the journal landing screen. Browse is explicit. No analytics, live AI, account login or cloud prayer storage is included.

## Run and build

Node.js 22 or later. No packages required.

```
node build.cjs
npm test
python -m http.server 8000 --directory public
```

`public/` is generated. Only the allowlisted browser assets are copied. For the test harness:

```
EVIDENCE_DIR=./evidence python tests/redesign-browser.py
```

The harness requires Python Playwright and Chromium. It uses DOM injection with simulated localStorage, tab handoff and provider responses because local browser HTTP navigation was blocked in the development environment. Blob downloads are real. This is not native Safari/VoiceOver or live service evidence.

## ESV reader - configuration still required

Set **ESV_API_KEY** as a secret server-side environment variable in the Vercel `prayer` project's **Preview** environment, then redeploy the preview. Obtain your own application key and review the conditions at https://api.esv.org/. Do not put a key in browser code, Git, screenshots or chat.

Until configured, the reader shows a clear unavailable-text state. Context notes are labelled editorial and never substituted as ESV text. The API accepts only one of 15 public catalogue IDs (35 verses across those ranges), never arbitrary references or journal content. It has a bounded warm-instance cache and request guard; Crossway enforces account-wide limits. A deployment's HTTP/proxy configuration and provider access still require live verification.

The ESV text is supplied by Crossway, not bundled or relicensed with this GPL source. It is not included in journal backups or HTML reading copies. Full API terms: https://api.esv.org/ and general permissions: https://www.crossway.org/permissions/.

## Storage and history

`core.js` retains the v2 model unchanged for migration. `journal.js` uses schema **3**, unrelated to app build numbering. Existing v2 entries are read in memory; only an explicit Save writes a v3 copy. Original v2 and v1 data is retained for rollback, not silently deleted. JSON restore adds missing IDs and skips existing IDs without overwriting them. Never confuse hidden journal excerpts with encryption.

Editing preserves the previous wording as a revision; follow-ups are linked entries. Prayer date, creation and last update are distinct. Request status is the writer's assessment. Thanksgiving never automatically answers a request. Journals on preview and production origins do not synchronise.

## Build identity

`release.json` is the single numbering source. Its first revised-format build is **0.0.001**, not a reconstruction of historical deployment counts. Increase `build` for the next release candidate. `packageVersion` remains valid SemVer. Vercel inserts the actual Git commit and UTC build time into generated `build-info.js`; source is labelled unavailable when not supplied locally.

## Scope and safeguards

No spiritual scoring, divine verdict, salvation assessment, forced completion or automatic overwriting of prayer wording. The founding About text and all twelve poem lines remain intact. All built-in Scripture links resolve through the shared catalogue. Logos opens separately and is not connected to an owned library.

Production must not be changed until the preview is explicitly approved. The existing GPL-3.0 licence is retained.
