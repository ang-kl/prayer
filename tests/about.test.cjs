'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const A = require('../about.js');
const C = require('../core.js');
const root = path.join(__dirname, '..');
const expectedPoem = [
  'Inside the quiet chambers of the chest,',
  'The Heart beats out its steady, sacred drum,',
  'While Emotions rise like oceans, manifest,',
  'Stirring the deep where quiet shadows come.',
  'The Will stands firm, a beacon in the night,',
  'Guiding the steps through storms that wildly roll,',
  'As the sharp Mind unravels dark to light,',
  'All held within the eternal, breathing Soul.',
  'When these five rivers gather and collide,',
  'The fragile banks of ordinary break;',
  'We are whelmed beneath the brilliant, rising tide,',
  'Alive to every truth they leave awake.'
];
const html = A.content();
test('Preserves all 12 original poem lines exactly', () => assert.deepEqual([...A.POEM], expectedPoem));
test('Retains the approved app description', () => assert.equal(A.DESCRIPTION, C.DESCRIPTION));
test('Separates origin text, anonymous LLM material and editorial explanation', () => {
  for (const s of ['another LLM','not a verbatim transcript','not a biblical definition','does not establish that no one else','not presented as Scripture or a historic Christian prayer']) assert.ok(html.includes(s),s);
});
test('Retains HEWMS, WHEMS, and the original Soul concern', () => {
  for(const s of ['HEWMS','WHEMS','Saved or Slave to Sin','saved by Christ and freed to serve God']) assert.ok(html.includes(s),s);
});
test('Includes every WHEMS invitation with its Scripture reference', () => {
  for(const area of C.AREAS) assert.ok(html.includes(area.name),area.name);
  for(const ref of ['Luke+22:42','Psalm+139:23-24','Matthew+26:37-39','Romans+12:1-2','Ephesians+2:8-10']) assert.ok(html.includes(ref),ref);
});
test('Keeps mixed thanksgiving/request and no-majority-vote safeguards', () => {
  for(const s of ['same prayer','same area','not a majority vote','not a fifth performance score','not live AI calls']) assert.ok(html.includes(s),s);
});
test('All source links are HTTPS and use safe new-tab attributes', () => {
  const links=[...html.matchAll(/<a href="([^"]+)"([^>]*)>/g)];assert.ok(links.length>15);
  const allowed=new Set(['www.esv.org','www.stepbible.org','www.blueletterbible.org','app.logos.com']);
  for(const [,url,attrs] of links){assert.equal(new URL(url).protocol,'https:');assert.ok(allowed.has(new URL(url).hostname));assert.ok(attrs.includes('noopener noreferrer'));}
});
test('Editorial content contains no script, embed or inline event handler', () => {
  assert.doesNotMatch(html,/<(?:script|iframe|form)\b/i);assert.doesNotMatch(html,/\son\w+\s*=/i);
});
test('One optional panel; not another prayer step', () => {
  assert.equal((html.match(/<details\b/g)||[]).length,8);
  const index=fs.readFileSync(path.join(root,'index.html'),'utf8');
  assert.ok(index.includes('data-about-open'));assert.ok(index.includes('aria-haspopup="dialog"'));
  assert.ok(index.includes('src="about.js"'));assert.ok(index.includes('href="about.css"'));
});
test('Prayer, journal, exporter, licence and existing styles are byte-unchanged', () => {
  const hashes={'app.js':'9e06ba516bf7361154c6838b7c4ac40ec484edf3','core.js':'136e86c3e5223f03a428ff23f2a383208f7821a3','export.js':'3221756e43898b85f7cff06f697f57f3e639ffbe','styles.css':'397268589643886a4da1a389170fdd1101b9de2d','export-view.css':'e1c5893064c762314c74c872bcd7c5f81d4ba279','LICENSE':'f288702d2fa16d3cdf0035b15a9fcbc552cd88e7'};
  for(const [file,expected] of Object.entries(hashes)){
    const data=fs.readFileSync(path.join(root,file));
    const actual=crypto.createHash('sha1').update(`blob ${data.length}\0`).update(data).digest('hex');assert.equal(actual,expected,file);
  }
});
