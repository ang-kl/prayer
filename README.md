# Wholehearted

Project: `prayer` · Method: W.H.E.M.S. Prayer · Version: 2.0

W.H.E.M.S. Prayer brings our Will, Heart, Emotions, Mind and Soul before God when seeking his help and direction. We thank him for the areas he has already shaped and ask him to transform the areas that are still struggling, so that our decision and response honour Christ.

## Run

No application dependencies, account, database, AI API or environment variables.

```sh
node build.cjs
python3 -m http.server 8000 --directory public
```

Open `http://localhost:8000`. Vercel settings are in `vercel.json`: an empty install command and a dependency-free static build publishing only four browser assets.

## What changed

The UI, state model, prayer composer and storage code were rewritten, rather than patched over v1. Each area accepts thanksgiving, a request, both, or neither. Written reflections are included in an editable prayer. Thanksgiving can start without a saved entry. Returning to a prayer creates a linked new entry without rewriting the original.

The journal holds up to 100 local entries. Saving is explicit. Errors, quota failures, corrupt data and stale snapshots do not silently produce a successful-save message. Importing v1 is optional and preserves the original `wholehearted-prayer-v1` storage value. Exported files contain personal data and should be kept private. Backup export is provided; v2 backup-file re-import is not implemented yet.

## Source and theological boundaries

ESV.org reading links; STEP Bible and Blue Letter Bible passage-study links; Logos opens separately in the user's browser. There is no authenticated Logos integration, live Scripture API or automatic lexical retrieval. On-screen passage summaries and W.H.E.M.S. assignments are teaching applications, not verbatim Scripture or new revelation.

No spiritual scores, salvation classifier, emotional-peace verdict or automatic decision approval. Soul is foundational; the app does not assume a person's faith. All nine fruits remain available without exclusive assignments. Revisit dates do not schedule notifications.

## Privacy

Application reflections never leave the browser through this code. The hosting service receives ordinary page requests. External sources are visited only when links are opened, with no reflections in the URL. Local storage is not encrypted by the app, not a cloud backup, and is separate for each browser/origin. Unsaved drafts are lost on reload. No analytics or external runtime scripts are included.

## Tests

```sh
node --test tests/core.test.cjs
# Optional UI testing only: install Python Playwright and a Chromium browser.
python3 tests/browser.py
# For environments that block browser navigation:
BROWSER_MODE=dom python3 tests/browser.py
```

Tested on Node 22 and Chromium: 31 logic tests; 18 UI scenarios; widths 320, 390, 430, 768, 1024 and 1440. The recorded UI run used DOM mode: real app assets injected into Chromium with a storage fixture. This does not verify live networking, native browser persistence, response headers or Safari. The default HTTP mode is provided for those checks in an unrestricted environment.

`core.js` contains content, pure logic and storage helpers; `app.js` renders the UI; `styles.css` handles responsive layouts. No production deployment or main-branch replacement is authorised by this review branch. Existing GPL-3.0 licence retained unchanged.
