'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const A=require('../about.js'),C=require('../core.js'),S=require('../catalogue.js');
const html=A.content();
const src=file=>fs.readFileSync(path.join(__dirname,'..',file),'utf8');
test('About contains no personal attribution or conversation-development narrative',()=>{
  assert.doesNotMatch(src('about.js'),/Adrian|Chat\s*p?GPT|OpenAI|\bLLM\b|language model|founding conversation|September 2026|HEWMS/i);
  assert.ok(html.includes('A simple background'));
  assert.ok(html.includes('You do not need polished words or settled feelings to begin.'));
});
test('The approved purpose remains word-for-word and is not replaced by invented history',()=>{
  assert.ok(html.includes(C.DESCRIPTION));
  assert.doesNotMatch(html,/founded by|created by|written by|ancient tradition|centuries.old/i);
});
test('All five invitations are visible without disclosure controls',()=>{
  assert.equal((html.match(/<dt>/g)||[]).length,5);
  for(const a of C.AREAS)assert.ok(html.includes(a.name));
  const group=html.slice(html.indexOf('<dl'),html.indexOf('</dl>'));
  assert.doesNotMatch(group,/<details\b|\shidden(?:\s|=|>)/i);
  assert.ok(html.indexOf('<details')>html.indexOf('</dl>'));
});
test('The sole optional section is the poem; core guidance is not hidden',()=>{
  assert.equal((html.match(/<details\b/g)||[]).length,1);
  assert.match(html,/<summary>A reflective poem<\/summary>/);
  assert.doesNotMatch(html,/<details[^>]*\bopen\b/);
});
test('Every Scripture link remains resolvable by the in-page reference reader',()=>{
  const refs=[...html.matchAll(/href="(https:\/\/www\.esv\.org\/verses\/[^"]+)"/g)].map(m=>S.fromURL(m[1]));
  assert.equal(refs.length,8);assert.ok(refs.every(Boolean));
  assert.doesNotMatch(html,/target="_blank"/);
});
test('Mixed prayer, grace and scriptural authority remain explicit',()=>{
  for(const phrase of ['Both can belong in the same prayer','Salvation is his gift by grace through faith','Scripture remains the authority','not a spiritual score','not Scripture, a historical prayer'])assert.ok(html.includes(phrase),phrase);
});
test('About is static text, with no script, data access or external processing',()=>{
  assert.doesNotMatch(html,/<script|<iframe|<form\b|\son[a-z]+=/i);
  assert.doesNotMatch(src('about.js'),/localStorage|sessionStorage|\bfetch\(|XMLHttpRequest/);
});
test('AI consent, journal persistence, prayer logic and privacy implementation are unchanged',()=>{
  const hashes={
    'app.js':'85ab6b98f1928a8f9c3a7ec4fde3cd5a7dc7dcc6',
    'journey-ui.js':'b5c6dac6b4bf11936a877aa5bb3b6e825cd3a2ff',
    'api/guidance.js':'c976b7786f4d0168ee05139ec09e823de3053757',
    'api/scripture.js':'1d84ac4eb9ccfcfb71e44b0fd7cdb3981976a10c',
    'core.js':'136e86c3e5223f03a428ff23f2a383208f7821a3',
    'journal.js':'b31725369d97511edac8cc826263eb55799c934e',
    'guidance-core.js':'c33f1ab1ae7fabd4d20782dc0cb494e4a03ed881',
    'export.js':'5b1dcc2648717337be04bb26eea82c226997a5ed',
    'styles.css':'f968c7269644d2ebf0d195f37c4e55f64aab0d2d',
    'catalogue.js':'5277b0957469c32b639a2faa07a2d9bb3652bbb3',
    'LICENSE':'f288702d2fa16d3cdf0035b15a9fcbc552cd88e7'
  };
  for(const [file,expected] of Object.entries(hashes)){
    const b=fs.readFileSync(path.join(__dirname,'..',file));
    const actual=crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex');
    assert.equal(actual,expected,file);
  }
  assert.match(src('journey-ui.js'),/I agree to send the current issue and replies for AI guidance/);
});
