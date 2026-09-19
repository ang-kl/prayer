/* Readable, script-free HTML copies. No prayer data or files are uploaded. */
(function (root) {
  'use strict';
  const C = typeof module === 'object' && module.exports ? require('./core.js') : root.WholeheartedCore;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const link = (url, label) => `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`;
  const para = value => `<p class="export-text">${esc(value)}</p>`;
  const stamp = value => {
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? 'Date not recorded' : new Intl.DateTimeFormat('en-SG', {
      dateStyle:'medium', timeStyle:'short', timeZone:'Asia/Singapore'
    }).format(d) + ' SGT';
  };
  function filename(raw) {
    const d = C.normalise(raw), time = new Date(d.updatedAt || d.createdAt);
    const date = Number.isNaN(time.getTime()) ? 'undated' : new Intl.DateTimeFormat('en-CA', {
      year:'numeric', month:'2-digit', day:'2-digit', timeZone:'Asia/Singapore'
    }).format(time);
    // Do not put the personal matter or names in a filename.
    return `Wholehearted-${d.mode === 'thanks' ? 'Thanksgiving' : 'Prayer'}-${date}-${d.id.slice(-8)}.html`;
  }
  function article(raw, heading = 'h1') {
    const d = C.normalise(raw), h = heading === 'h2' ? 'h2' : 'h1';
    const mode = d.parentId ? 'Return to prayer' : d.mode === 'thanks' ? 'Thanksgiving' : 'Seeking help';
    const section = (title, body) => `<section class="export-section"><h2>${title}</h2>${body}</section>`;
    const reflections = C.AREAS.map(a => {
      const r = d.areas[a.key];
      const thanks = r.thank ? `<h4>Thanksgiving</h4>${para(r.thankNote.trim() || 'Thanksgiving selected; no additional note recorded.')}` : '';
      const asks = r.ask ? `<h4>Request for help</h4>${para(r.askNote.trim() || 'Help requested; no additional note recorded.')}` : '';
      return `<section class="export-area"><h3>${a.key} · ${a.name}</h3>${thanks}${asks}${!r.thank && !r.ask ? '<p>No reflection selected.</p>' : ''}<p class="export-sources">${link(C.esv(a.passage), a.passage + ' · ESV')} · ${link(C.step(a.step), 'STEP Bible')} · ${link('https://www.blueletterbible.org/esv/' + a.blb + '/', 'Blue Letter Bible')}</p></section>`;
    }).join('');
    const sourceLinks = [
      link('https://www.esv.org/', 'ESV.org'), link('https://www.stepbible.org/', 'STEPBible.org'),
      link('https://www.blueletterbible.org/', 'Blue Letter Bible'), link('https://app.logos.com/', 'Logos account')
    ].join(' · ');
    return `<article class="export-sheet">
<header class="export-heading"><p class="export-brand">Wholehearted · W.H.E.M.S. Prayer</p><p>${mode}</p><${h}>${esc(d.topic || 'My prayer')}</${h}><p class="export-meta">Entry created: ${esc(stamp(d.createdAt))}<br>Entry updated: ${esc(stamp(d.updatedAt))}</p></header>
${d.context ? section('What I am bringing to God', para(d.context)) : ''}
${section('My prayer', para(d.prayer ?? C.compose(d)))}
${section('My Scripture reflection', (d.gate ? `<p><strong>My recorded understanding:</strong> ${esc(C.GATES[d.gate][0])}</p>` : '') + para(d.scripture || 'No additional Scripture reflection recorded.'))}
${section('My W.H.E.M.S. reflections', reflections)}
${d.fruit.length ? section('Fruit I am asking the Spirit to grow', para(d.fruit.join(' · ')) + `<p>${link(C.esv('Galatians 5:22-25'), 'Galatians 5:22-25 · ESV')}</p>`) : ''}
${section('My next faithful step', para(d.nextStep || 'No next step recorded.') + (d.revisit ? `<p>Revisit: ${esc(d.revisit)}. No reminder is scheduled.</p>` : ''))}
${d.legacyNote ? section('Earlier thanksgiving note', para(d.legacyNote)) : ''}
${section('Study sources', `<p class="export-sources">${sourceLinks}</p><p>These are study links, not live retrieval or lexical verification. Logos opens separately; this app does not access your library. External links need internet access.</p>`)}
<footer class="export-footer"><p>A prayer aid, not a message from God. Scripture remains the authority. W.H.E.M.S. is a teaching aid, not a score or an assessment of salvation.</p><p>Private prayer copy. Keep it secure and share only deliberately. This readable HTML copy does not restore entries into the journal.</p></footer>
</article>`;
  }
  const CSS = `
*{box-sizing:border-box}html{color-scheme:light}body{margin:0;background:#f7f7f3;color:#172c25;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:18px;line-height:1.65}.export-sheet{max-width:820px;margin:32px auto;padding:36px;background:#fff;border:1px solid #c9d0ca;border-radius:18px;overflow-wrap:anywhere}.export-heading{border-bottom:2px solid #183c32;padding-bottom:16px}.export-brand{font-weight:750;letter-spacing:.03em}.export-meta,.export-footer{font-size:.88em;color:#47574f}h1{font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2}h2{font-size:1.35rem;line-height:1.3;margin:0 0 12px}h3{font-size:1.1rem;margin:0}h4{font-size:1rem;margin:12px 0 0}.export-section{margin-top:28px}.export-text{white-space:pre-wrap;overflow-wrap:anywhere}.export-area{border-left:3px solid #b2c3b8;padding:4px 0 4px 16px;margin:20px 0}.export-sources{font-size:.88em;line-height:2}a{color:#173f32;text-decoration:underline;text-underline-offset:3px}a:focus-visible{outline:3px solid #172c25;outline-offset:4px}.export-footer{border-top:1px solid #c9d0ca;margin-top:32px;padding-top:14px}@media(max-width:600px){body{font-size:17px}.export-sheet{margin:0;border:0;border-radius:0;padding:24px 18px}}@media print{@page{size:A4;margin:16mm}body{background:white;color:black;font-size:11pt}.export-sheet{margin:0;max-width:none;border:0;padding:0}h1,h2,h3,h4{break-after:avoid}.export-area{break-inside:avoid}a{color:inherit}.export-footer{color:inherit}}
`;
  function html(raw) {
    const d = C.normalise(raw);
    return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Wholehearted · ${esc(d.topic || 'My prayer')}</title><style>${CSS}</style></head><body>${article(d)}</body></html>`;
  }
  const api = {filename, article, html};
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.WholeheartedExport = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
