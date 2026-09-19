'use strict';
const test=require('node:test'), assert=require('node:assert/strict');
const C=require('../core.js'), X=require('../export.js');
function fixture(){
  const d=C.blank('seek','2026-09-19T04:00:00Z','test-export-12345678');
  d.topic='Respond to an unfair comment';d.context='I want to answer responsibly.';
  d.areas.W.thank=true;d.areas.W.thankNote='willingness to listen';
  d.areas.H.ask=true;d.areas.H.askNote='a motive that seeks their good';
  d.areas.E.thank=true;d.areas.E.thankNote='strength to pause';
  d.areas.E.ask=true;d.areas.E.askNote='gentleness while I am still hurt';
  d.scripture='James 1:19 - listen before speaking.';d.fruit=['Gentleness','Self-control'];
  d.nextStep='Speak privately after listening.';d.revisit='2026-09-21';
  d.prayer='Father, help me listen.\nKeep my words kind. Amen.';return d;
}
test('HTML is a complete UTF-8, responsive, self-contained document',()=>{
  const h=X.html(fixture());assert.match(h,/^<!doctype html>/);assert.match(h,/<meta charset="utf-8">/);assert.match(h,/name="viewport"/);assert.match(h,/<style>/);assert.match(h,/<\/html>$/);
});
test('edited prayer and next step are preserved in the readable copy',()=>{
  const d=fixture(),h=X.html(d);assert.ok(h.includes(d.prayer));assert.ok(h.includes(d.nextStep));assert.ok(h.includes(d.scripture));assert.match(h,/No reminder is scheduled/);
});
test('both thanksgiving and requests in the same area are exported',()=>{
  const h=X.html(fixture());assert.match(h,/strength to pause/);assert.match(h,/gentleness while I am still hurt/);assert.match(h,/E · Emotions/);
});
test('unselected retained notes are excluded, not accidentally shared',()=>{
  const d=fixture();d.areas.S.thankNote='private deselected note';assert.ok(!X.html(d).includes('private deselected note'));
});
test('all user fields are escaped as text, never executable markup',()=>{
  const d=fixture(), attack='</style><img src=x onerror="alert(1)"><script>alert(1)</script>';
  d.topic=d.context=d.prayer=d.scripture=d.nextStep=d.legacyNote=d.areas.E.askNote=attack;
  const h=X.html(d);assert.ok(!h.includes(attack));assert.ok(!/<script\b|<img\b/i.test(h));assert.match(h,/&lt;script&gt;/);
});
test('the file needs no JavaScript, images, fonts or remote stylesheets',()=>{
  const h=X.html(fixture());assert.ok(!/<script\b|<link\b|<iframe\b|<img\b|<form\b|url\(/i.test(h));assert.match(h,/default-src 'none'/);assert.match(h,/name="referrer" content="no-referrer"/);
});
test('ESV, STEP Bible, BLB and Logos links remain labelled and external',()=>{
  const h=X.html(fixture());for(const host of ['www.esv.org','www.stepbible.org','www.blueletterbible.org','app.logos.com'])assert.ok(h.includes(host));assert.match(h,/rel="noopener noreferrer"/);assert.match(h,/not live retrieval or lexical verification/);
});
test('a generic safe HTML filename omits the personal matter',()=>{
  const d=fixture();d.topic='A name / sensitive: <secret>';const f=X.filename(d);assert.equal(f,'Wholehearted-Prayer-2026-09-19-12345678.html');assert.ok(!f.includes('secret'));
});
test('file date uses Singapore calendar date across UTC midnight boundary',()=>{
  const d=fixture();d.updatedAt='2026-09-19T17:00:00Z';assert.match(X.filename(d),/2026-09-20/);d.mode='thanks';assert.match(X.filename(d),/Wholehearted-Thanksgiving/);
});
test('HTML generation never mutates a saved record',()=>{
  const d=fixture(), before=JSON.stringify(d);X.html(d);X.article(d,'h2');X.filename(d);assert.equal(JSON.stringify(d),before);
});
test('preview heading can be nested without adding a second h1',()=>{
  const h=X.article(fixture(),'h2');assert.ok(!h.includes('<h1>'));assert.match(h,/<h2>Respond to an unfair comment<\/h2>/);
});
test('invalid IDs are rejected and missing dates are labelled honestly',()=>{
  const d=fixture();d.updatedAt='';d.createdAt='';assert.match(X.filename(d),/undated/);assert.match(X.html(d),/Date not recorded/);assert.throws(()=>X.html({...d,id:'../bad'}));
});
test('blank notes never produce an invented salvation or improvement verdict',()=>{
  const d=C.blank('thanks','2026-09-19T04:00:00Z','thanks');d.topic='Today';const h=X.html(d);assert.match(h,/No reflection selected/);assert.ok(!h.includes('someone who belongs to him'));assert.ok(!h.includes('God says'));
});
