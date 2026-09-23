'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const A=require('../about.js'),C=require('../core.js'),S=require('../catalogue.js');
const html=A.content(),src=file=>fs.readFileSync(path.join(__dirname,'..',file),'utf8');
test('About contains no personal attribution or conversation-development narrative',()=>{assert.doesNotMatch(src('about.js'),/Adrian|Chat\s*p?GPT|OpenAI|\bLLM\b|language model|founding conversation|September 2026|HEWMS/i);assert.ok(html.includes('A simple background'));assert.ok(html.includes('You do not need polished words or settled feelings to begin.'));});
test('The approved purpose remains word-for-word without invented history',()=>{assert.ok(html.includes(C.DESCRIPTION));assert.doesNotMatch(html,/founded by|created by|written by|ancient tradition|centuries.old/i);});
test('All five About invitations remain visible without disclosure controls',()=>{assert.equal((html.match(/<dt>/g)||[]).length,5);for(const a of C.AREAS)assert.ok(html.includes(a.name));assert.doesNotMatch(html.slice(html.indexOf('<dl'),html.indexOf('</dl>')),/<details\b|\shidden(?:\s|=|>)/i);});
test('The sole optional About section is the poem',()=>{assert.equal((html.match(/<details\b/g)||[]).length,1);assert.match(html,/<summary>A reflective poem<\/summary>/);assert.doesNotMatch(html,/<details[^>]*\bopen\b/);});
test('Every About reference resolves to the existing in-page reader',()=>{const refs=[...html.matchAll(/href="(https:\/\/www\.esv\.org\/verses\/[^"]+)"/g)].map(m=>S.fromURL(m[1]));assert.equal(refs.length,8);assert.ok(refs.every(Boolean));assert.doesNotMatch(html,/target="_blank"/);});
test('Mixed prayer, grace and Scripture authority remain explicit',()=>{for(const phrase of ['Both can belong in the same prayer','Salvation is his gift by grace through faith','Scripture remains the authority','not a spiritual score','not Scripture, a historical prayer'])assert.ok(html.includes(phrase),phrase);});
test('About remains static text with no data access or external processing',()=>{assert.doesNotMatch(html,/<script|<iframe|<form\b|\son[a-z]+=/i);assert.doesNotMatch(src('about.js'),/localStorage|sessionStorage|\bfetch\(|XMLHttpRequest/);});
test('About, Scripture API, journal schema, core theology, catalogue and licence remain byte-unchanged',()=>{
// UI, output parsing and the guidance endpoint intentionally change; these boundaries do not.
const hashes={'about.js':'ca1bd2b105039e345ca19b234715d6e66dbabfcd','api/scripture.js':'1d84ac4eb9ccfcfb71e44b0fd7cdb3981976a10c','core.js':'136e86c3e5223f03a428ff23f2a383208f7821a3','journal.js':'b31725369d97511edac8cc826263eb55799c934e','catalogue.js':'5277b0957469c32b639a2faa07a2d9bb3652bbb3','LICENSE':'f288702d2fa16d3cdf0035b15a9fcbc552cd88e7'};
for(const [file,expected]of Object.entries(hashes)){const b=fs.readFileSync(path.join(__dirname,'..',file));assert.equal(crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex'),expected,file);}
assert.match(src('journey-ui.js'),/I agree to send the current issue and replies for AI guidance/);
});
