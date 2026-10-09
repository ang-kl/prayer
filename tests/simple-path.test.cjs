'use strict';
/* Simple-path (Lamp Path) contract for the Pray screen redesign, spec
   doc/Feature/2026-10-09-pray-ui-redesign.md. Static and unit checks only: every test name starts
   with the check id that the spec's acceptance criteria and invariants cite. The checks read the
   repository sources and render journey-ui.js in Node with the helpers that app.js passes to it
   (extracted from app.js, so a change there fails loudly), so journey-ui.js must stay loadable as a
   plain script outside a browser (document and matchMedia are stubbed). No build, network or storage
   is needed; public/ is not read. Browser behaviour is covered by tests/simple-path-browser.py. */
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ROOT=path.join(__dirname,'..');
const read=f=>fs.readFileSync(path.join(ROOT,f),'utf8');
const C=require('../core.js'),S=require('../catalogue.js'),J=require('../journal.js'),G=require('../guidance-core.js'),T=require('../theme.js'),P=require('../prayer-output.js'),TE=require('../teaching.js');
const KEYS=['W','H','E','M','S'],NAMES={W:'Will',H:'Heart',E:'Emotions',M:'Mind',S:'Soul'};
const SAVE_PROMISE='Your words stay only on this page until you tap Save.';
const CONSENT='I agree to send the current issue and replies for AI guidance.';
const BROWSER_SOURCES=['index.html','app.js','journey-ui.js','experience.js','teaching.js','theme.js','guidance-core.js','prayer-output.js'];
const CSS_SOURCES=()=>({'theme.js (css)':T.css,'styles.css':read('styles.css'),'experience.css':read('experience.css')});
const QUESTION_ISSUE='Should I talk to my daughter or pray as she struggles with research?';
const STATEMENT_ISSUE='I am worried about my son starting a new job far from home.';
/* A14: the five core questions keep today's on-screen wording (journey-ui.js:7). */
const QUESTIONS={W:'What action are you considering, and what would it seek to accomplish?',H:'What good are you hoping for, and for whom?',E:'What are you feeling, and what have other people actually expressed?',M:'What do you know, and what are you presently assuming?',S:'How does your relationship with Christ bear on this matter?'};
/* A12: the teaching text stays word for word; only its markup (the example-prayer fold) may change. */
const TEACHING_TEXT={intro:'A simple W.H.E.M.S. prayer pattern During conflict W: Lord, what do I want, and does it honour You? H: What is ruling my heart beneath this disagreement? E: Here is what I feel. Keep these feelings from ruling me. M: Show me what is true, what Scripture says, and where my assumptions may be wrong. S: I belong to Christ. Let me respond as one saved by grace rather than as a slave to pride, fear or sin. Afterwards - thanksgiving W: Thank You for directing me. H: Thank You for shaping me. E: Thank You for sustaining me. M: Thank You for teaching me. S: Thank You that I am Yours by grace.',
 guardrails:'Guardrails W.H.E.M.S. serves Scripture - it does not control Scripture. Start with the passage, then use W.H.E.M.S. to organise prayer and self-examination. Soul = Saved or Slave to Sin works here as an allegiance check, but do not use it to label another believer\'s hidden spiritual state without textual warrant. Emotion is real but not sovereign. Acts 15 records dissension and sharp disagreement without making emotional intensity the test of truth. Mind is not cold rationalism. Acts 15 combines testimony, Scripture, corporate deliberation and dependence on God. Thanksgiving is more than relief. Thank God for what He changes in us, not only for changing circumstances.',
 summary:'1-line Summary In conflict, bring your Will, Heart, Emotions, Mind and Soul before God; after His direction becomes clearer, bring the same five areas back to Him in thanksgiving.'};

/* ---------- a small HTML reader (enough for the app's own templates; not a general parser) ---------- */
const VOID=new Set(['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']);
function decode(s){return s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi,(m,e)=>e[0]==='#'?String.fromCodePoint(/^#x/i.test(e)?parseInt(e.slice(2),16):parseInt(e.slice(1),10)):({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '}[e.toLowerCase()]??m));}
function parse(html){
 const doc={tag:'#root',attrs:{},children:[],parent:null};let cur=doc;
 const re=/<!--[\s\S]*?-->|<!doctype[^>]*>|<(\/?)([a-zA-Z][\w:-]*)((?:\s+[^\s=>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>"']+))?)*)\s*(\/?)>|([^<]+)|</gi;
 let m;
 while((m=re.exec(html))){
  if(m[5]!==undefined){cur.children.push({text:decode(m[5]),parent:cur});continue;}
  if(!m[2]){if(m[0]==='<')cur.children.push({text:'<',parent:cur});continue;}
  const tag=m[2].toLowerCase();
  if(m[1]){let n=cur;while(n&&n.tag!==tag)n=n.parent;if(n&&n.parent)cur=n.parent;continue;}
  const attrs={};for(const a of (m[3]||'').matchAll(/([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g))attrs[a[1].toLowerCase()]=decode(a[2]??a[3]??a[4]??'');
  const node={tag,attrs,children:[],parent:cur};cur.children.push(node);
  if(!VOID.has(tag)&&!m[4])cur=node;
 }
 return doc;
}
function* walk(n){yield n;for(const c of n.children||[])yield* walk(c);}
const els=n=>[...walk(n)].filter(x=>x.tag&&x.tag!=='#root');
const textNodes=n=>[...walk(n)].filter(x=>'text' in x);
const textOf=(n,skipTag=()=>false)=>textNodes(n).filter(t=>!up(t).some(a=>skipTag(a))).map(t=>t.text).join('');
/* The words of a fragment with element boundaries treated as spaces (for comparing prose). */
const wordsOf=(n,skipTag=()=>false)=>norm(textNodes(n).filter(t=>!up(t).some(a=>skipTag(a))).map(t=>t.text).join(' '));
const norm=s=>String(s).replace(/\s+/g,' ').trim();
const cls=n=>(n.attrs?.class||'').split(/\s+/).filter(Boolean);
const byId=(r,id)=>els(r).find(n=>n.attrs.id===id);
/* Ancestors from the node itself (elements only) up to, but not including, the root. */
const up=n=>{const a=[];for(let p=n.tag?n:n.parent;p&&p.tag!=='#root';p=p.parent)a.push(p);return a;};
const order=r=>{const list=[...walk(r)];return n=>list.indexOf(n);};
/* Words a reader sees: skips form values, <option> lists, <script>, <style> and <title>. */
function visibleText(r,skip=()=>false){return norm(textNodes(r).filter(t=>!up(t).some(a=>['textarea','script','style','title','option','select'].includes(a.tag)||skip(a))).map(t=>t.text).join(' '));}
/* A label's own words, without the field it wraps. */
function ownText(n){return norm(textNodes(n).filter(t=>!up(t).slice(0,up(t).indexOf(n)).some(a=>['textarea','select','option','input'].includes(a.tag))).map(t=>t.text).join(' '));}
const inDetailsOrHidden=chain=>chain.some(x=>x.tag==='details'||'hidden' in x.attrs);
/* The chain from a node up to and including the ancestor `stop`. */
const chainTo=(n,stop)=>{const u=up(n);const i=u.indexOf(stop);return i<0?u:u.slice(0,i+1);};

/* ---------- rendering the Pray route in Node ---------- */
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let helperCache=null;
/* The helpers app.js passes to WholeheartedJourneyUI.render, extracted from app.js itself so that
   drift between the real page and this render fails here instead of passing silently. */
function appHelpers(){
 if(helperCache)return helperCache;
 const app=read('app.js');
 const call=app.match(/WholeheartedJourneyUI\.render\(\s*d\s*,\s*\{([^}]*)\}\s*\)/);
 assert.ok(call,'app.js no longer calls WholeheartedJourneyUI.render(d,{...}); the Node render mirror cannot follow it');
 const keys=call[1].split(',').map(s=>s.trim().split(':')[0].trim()).filter(Boolean);
 const known=['field','input','options','ref','btn','byReference','localInput','statuses'];
 const extra=keys.filter(k=>!known.includes(k));
 assert.deepEqual(extra,[],'app.js passes render helpers this test does not mirror ('+extra.join(', ')+'); extend the mirror with the owner (F7)');
 const src=[];
 for(const n of ['btn','ref','field','input']){const m=app.match(new RegExp('^const '+n+'=.*;$','m'));assert.ok(m,'app.js helper "'+n+'" is no longer a one-line const; the Node render mirror cannot extract it');src.push(m[0]);}
 const o=app.match(/^function options\(map,selected\)\{.*\}$/m);assert.ok(o,'app.js helper "options" moved; the Node render mirror cannot extract it');src.push(o[0]);
 const ctx={S,J,esc};vm.createContext(ctx);
 vm.runInContext(src.join('\n')+'\nthis.h={btn,ref,field,input,options};',ctx,{filename:'app.js (helpers)'});
 helperCache={...ctx.h,byReference:S.byReference,localInput:J.localInput,statuses:J.STATUSES};
 return helperCache;
}
function helpers(misses){
 const u=appHelpers();
 return new Proxy(u,{get:(t,k)=>{if(k in t)return t[k];if(typeof k==='string')misses.add(k);return ()=> '';}});
}
function guide(){return {summary:'You want to support an adult daughter who asked you to listen.',statedFacts:['She asked you to listen.'],uncertainties:['Her plans are unknown.'],clarification:'What has she asked for?',areas:KEYS.map((key,i)=>({key,focus:'An aspect of supporting your daughter.',question:'What does '+NAMES[key]+' invite you to consider?',followup:'Consider what she has actually requested.',referenceIds:[S.items[i].id]})),options:[{action:'Offer a listening conversation.',reason:'She requested listening.',caution:'Do not turn it into advice.',referenceIds:['proverbs-15-22']}],safetyNote:'If anyone is in danger, contact emergency services.'};}
function loadJourney(){
 if(globalThis.WholeheartedJourneyUI)return globalThis.WholeheartedJourneyUI;
 // Minimal browser stubs: render() must not need them, but a module may touch them while loading.
 globalThis.document??={querySelector:()=>null,querySelectorAll:()=>[],getElementById:()=>null,addEventListener(){},removeEventListener(){},createElement:()=>({style:{},dataset:{},setAttribute(){},append(){},classList:{add(){},remove(){}}}),documentElement:{dataset:{},style:{setProperty(){}},classList:{add(){},remove(){}}},body:{append(){}}};
 globalThis.matchMedia??=()=>({matches:false,addEventListener(){},removeEventListener(){}});
 globalThis.requestAnimationFrame??=fn=>setTimeout(fn,0);
 Object.assign(globalThis,{WholeheartedCore:C,WholeheartedScripture:S,WholeheartedJournal:J,WholeheartedGuidance:G,WholeheartedPrayerOutput:P,WholeheartedTeaching:TE,WholeheartedExperience:{}});
 try{vm.runInThisContext(read('journey-ui.js'),{filename:'journey-ui.js'});}
 catch(e){assert.fail('journey-ui.js must stay loadable as a plain script so its render() can be checked in Node: '+e.message);}
 assert.equal(typeof globalThis.WholeheartedJourneyUI?.render,'function','journey-ui.js no longer exposes WholeheartedJourneyUI.render');
 return globalThis.WholeheartedJourneyUI;
}
function draft(variant){
 const d=J.blank('mixed','2026-10-09T01:00:00Z','simple-path-fixture');
 if(variant==='guided'){d.journey.issue=QUESTION_ISSUE;d.journey.context='She is an adult.';d.journey.result=guide();d.journey.summary=guide().summary;d.journey.summaryConfirmed=false;d.journey.model='test fixture';for(const k of KEYS)d.journey.replies[k]='A reply for '+NAMES[k]+'.';d.areas.W.thank=true;d.areas.E.ask=true;d.prayerForms=G.local(d);d.prayer=d.prayerForms.whems;}
 return d;
}
const cache={};
function pray(variant='blank'){
 if(!cache[variant]){
  const misses=new Set();const html=loadJourney().render(draft(variant),helpers(misses));
  assert.deepEqual([...misses],[],variant+': render() requested helpers that app.js does not pass ('+[...misses].join(', ')+'); the real page would render them as undefined');
  cache[variant]={html,dom:parse(html)};
 }
 return cache[variant];
}
const VARIANTS=['blank','guided'];
/* Collects every breach so one run reports the whole gap, then fails once. */
function collector(){const fails=[];const ok=(cond,msg)=>{if(!cond)fails.push(msg);return !!cond;};ok.done=title=>assert.deepEqual(fails,[],title+':\n'+fails.join('\n'));ok.fails=fails;return ok;}
const index=()=>parse(read('index.html'));

/* ---------- a small CSS reader: rules with their @media context ---------- */
function cssRules(css){
 css=css.replace(/\/\*[\s\S]*?\*\//g,'');
 const out=[];
 (function walkCss(s,media){
  let i=0;
  while(i<s.length){
   const open=s.indexOf('{',i);if(open<0)break;
   const head=s.slice(i,open).replace(/^[\s;]+/,'').trim();
   let depth=1,j=open+1;while(j<s.length&&depth){if(s[j]==='{')depth++;else if(s[j]==='}')depth--;j++;}
   const body=s.slice(open+1,j-1);
   if(/^@(media|supports|container|layer)\b/i.test(head))walkCss(body,media.concat(head));
   else out.push({sel:head,body,media});
   i=j;
  }
 })(css,[]);
 return out;
}
const printOrForced=r=>r.media.some(m=>/\bprint\b|forced-colors/i.test(m));
const allRules=()=>Object.entries(CSS_SOURCES()).flatMap(([name,css])=>cssRules(css).map(r=>({...r,file:name})));
const rootSelector=sel=>sel.split(',').map(s=>s.trim());

/* ---------- colour helpers ---------- */
function hex(v){
 const s=String(v||'').trim().toLowerCase();
 if(s==='white')return '#ffffff';if(s==='black')return '#000000';
 const m=s.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/);if(!m)return null;let h=m[1];if(h.length===3)h=[...h].map(c=>c+c).join('');return '#'+h;
}
function luminance(h){return h.match(/[0-9a-f]{2}/gi).map(x=>parseInt(x,16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4).reduce((s,c,i)=>s+c*[.2126,.7152,.0722][i],0);}
function contrast(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
/* Effective global custom properties: :root and html rules outside print and forced-colours media,
   in cascade order (theme, styles, experience; :root beats html), later declarations winning. */
function tokens(){
 const map={},local=/^(area-tint|area-accent|vp-|tools-height|inset-)/;
 const rules=allRules().filter(r=>!printOrForced(r));
 for(const want of ['html',':root'])for(const r of rules){
  if(!rootSelector(r.sel).includes(want))continue;
  for(const m of r.body.matchAll(/(?:^|;)\s*--([\w-]+)\s*:\s*([^;]+)/g))if(!local.test(m[1]))map[m[1]]=m[2].trim();
 }
 const resolve=(v,seen=new Set())=>{const h=hex(v);if(h)return h;const r=String(v||'').trim().match(/^var\(\s*--([\w-]+)\s*(?:,\s*([^)]+))?\)$/);if(!r||seen.has(r[1]))return r?.[2]?hex(r[2]):null;seen.add(r[1]);return resolve(map[r[1]],seen)??(r[2]?hex(r[2]):null);};
 return {map,resolve};
}
/* Per-area accent and tint, from rules whose selector names the area (data-area=K or reflection-K). */
function areaColours(resolve){
 const areas={};
 for(const r of allRules()){
  if(printOrForced(r))continue;
  const k=(r.sel.match(/data-area=["']?([WHEMS])\b/)||r.sel.match(/reflection-([WHEMS])\b/))?.[1];
  if(!k)continue;
  for(const m of r.body.matchAll(/--(area-accent|area-tint)\s*:\s*([^;]+)/g)){const h=resolve(m[2].trim());if(h)areas[k]={...areas[k],[m[1]]:h};}
 }
 return areas;
}

/* ---------- checks ---------- */
test('areas_open_count: all five W.H.E.M.S. areas render open, in order, between the issue box and the prayers, each with a visible reply box and both choices; notes appear only when chosen (I5, I13, I1)',()=>{
 const ok=collector();
 for(const v of VARIANTS){
  const {dom}=pray(v),pos=order(dom);
  ok(!els(dom).some(n=>n.tag==='details'&&cls(n).includes('area')),v+': an area is a disclosure control');
  const areas=els(dom).filter(n=>n.tag==='section'&&cls(n).includes('area')&&cls(n).includes('open-area'));
  ok(areas.length===5,v+': expected exactly five open area sections, found '+areas.length);
  ok(JSON.stringify(areas.map(a=>a.attrs.id))===JSON.stringify(KEYS.map(k=>'reflection-'+k)),v+': areas out of order: '+areas.map(a=>a.attrs.id).join(', '));
  const issue=byId(dom,'guidance-issue'),prayers=byId(dom,'guide-prayers');
  if(!ok(issue&&prayers,v+': #guidance-issue or #guide-prayers missing'))continue;
  for(const a of areas){
   const k=a.attrs['data-area'];
   ok(pos(a)>pos(issue)&&pos(a)<pos(prayers),v+': '+a.attrs.id+' is not between the issue box and the prayers');
   ok(!inDetailsOrHidden(up(a)),v+': '+a.attrs.id+' is itself hidden or sits inside a closed or hidden container');
   const replies=els(a).filter(n=>n.tag==='textarea'&&n.attrs['data-guide-reply']===k);
   if(ok(replies.length===1,v+': '+a.attrs.id+' needs one reply box'))ok(!inDetailsOrHidden(chainTo(replies[0],a)),v+': the '+k+' reply box is inside a details or hidden element');
   for(const t of ['thank','ask']){
    const box=els(a).filter(n=>n.tag==='input'&&n.attrs['data-field']===`areas.${k}.${t}`);
    if(ok(box.length===1,v+': '+k+' '+t+' choice missing'))ok(!inDetailsOrHidden(chainTo(box[0],a)),v+': the '+k+' '+t+' choice is hidden');
    const note=els(a).find(n=>n.attrs['data-note']===k+'-'+t);
    if(ok(note,v+': '+k+' '+t+' note container missing')){
     const chosen=v==='guided'&&((k==='W'&&t==='thank')||(k==='E'&&t==='ask'));
     ok(chosen?!('hidden' in note.attrs):('hidden' in note.attrs),v+': the '+k+' '+t+' note must be '+(chosen?'shown when chosen':'hidden until chosen'));
    }
   }
  }
 }
 const labels=els(pray('guided').dom).filter(n=>'data-toc-label' in n.attrs).length;
 ok(labels===17,'the guided render has '+labels+' data-toc-label sections; tests/experience-browser.py:166 pins 19 Contents entries (17 sections plus start and end), so do not add or remove one');
 ok.done('open-area breaches');
});

test('no_progress_markup: no score, progress meter, badge or "x of 5" count in the Pray markup and copy (I6)',()=>{
 for(const v of VARIANTS){
  const {html,dom}=pray(v);
  assert.doesNotMatch(html,/<(progress|meter)\b|role="(progressbar|meter)"|aria-valuenow|aria-valuemax/i,v+': progress markup');
  for(const n of els(dom))for(const c of cls(n))assert.doesNotMatch(c,/^(progress|meter|score|badge|streak|stepper|achievement)/i,v+': class '+c);
  const text=visibleText(dom);
  assert.doesNotMatch(text,/\b\d+\s*(?:of|out of|\/)\s*(?:5|five)\b|\b(?:one|two|three|four|five)\s+(?:of|out of)\s+five\b|%\s*(?:complete|done)\b|\bstep\s+\d+\s+of\b/i,v+': a count of areas or steps');
  const plain=text.split(/(?<=[.!?])\s+/).filter(s=>!/\bnot\b|\bnever\b|\bno\b/i.test(s)).join(' ');
  assert.doesNotMatch(plain,/\b(?:score|scores|scored|badges?|streaks?|level up|achievements?|well done|great job|completed \d)\b/i,v+': gamified wording');
 }
 for(const f of ['journey-ui.js','experience.js','app.js','index.html'])assert.doesNotMatch(read(f),/<progress\b|<meter\b|progressbar|aria-valuenow|\bof 5\b|out of 5|answerRate|godliness score/i,f);
});

test('no_new_storage: app.js keeps its single journal write; no other browser source touches storage (I7, A10)',()=>{
 const app=read('app.js'),count=re=>(app.match(re)||[]).length;
 assert.equal(count(/\.setItem\(/g),1,'app.js must call .setItem( exactly once (the storage wrapper); any other write is new persistence');
 assert.equal(count(/localStorage\.setItem\(/g),1,'app.js must keep exactly one localStorage.setItem(');
 assert.equal(count(/localStorage\.getItem\(/g),1,'app.js must keep exactly one localStorage.getItem(');
 assert.doesNotMatch(app,/localStorage\s*\[|localStorage\.(?:removeItem|clear|key)\(|=\s*localStorage\b/,'app.js reaches localStorage outside its one getItem and one setItem');
 assert.ok(app.includes('Nothing is saved automatically'),'the "Nothing is saved automatically" promise is missing');
 const banned=/localStorage|sessionStorage|indexedDB|document\.cookie|caches\.open|serviceWorker|navigator\.storage|\.setItem\(/;
 for(const f of BROWSER_SOURCES.filter(f=>f!=='app.js'))assert.doesNotMatch(read(f),banned,f+' touches browser storage');
 assert.doesNotMatch(app,/sessionStorage|indexedDB|document\.cookie|caches\.open|serviceWorker|navigator\.storage/,'app.js uses a new storage mechanism');
 for(const f of BROWSER_SOURCES)assert.doesNotMatch(read(f),/(?:setItem|getItem|removeItem)\(\s*['"`]/,f+' uses a literal storage key');
});

test('csp_hygiene: no inline styles, inline scripts, handlers or web fonts; SVG uses presentation attributes only; the CSP header is unchanged (I9)',()=>{
 const vercel=JSON.parse(read('vercel.json')),csp=vercel.headers.flatMap(h=>h.headers).find(h=>h.key==='Content-Security-Policy')?.value;
 assert.equal(csp,"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-src https://www.esv.org; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",'vercel.json CSP changed');
 const page=read('index.html'),idx=parse(page);
 assert.doesNotMatch(page,/<style\b/i,'index.html has a <style> element');
 for(const n of els(idx)){
  assert.ok(!('style' in n.attrs),'index.html: style attribute on <'+n.tag+'>');
  for(const a of Object.keys(n.attrs))assert.doesNotMatch(a,/^on/,'index.html: inline handler '+a);
  if(n.tag==='script'){assert.ok(n.attrs.src,'index.html: inline <script>');assert.doesNotMatch(n.attrs.src,/^(https?:)?\/\//,'index.html: external script');}
  if(n.tag==='link'&&/stylesheet|preload|font/.test(n.attrs.rel||''))assert.doesNotMatch(n.attrs.href||'',/^(https?:)?\/\//,'index.html: external stylesheet or font');
  if(n.tag==='meta')assert.notEqual((n.attrs['http-equiv']||'').toLowerCase(),'content-security-policy','index.html: a meta CSP would diverge from vercel.json');
  for(const val of Object.values(n.attrs))assert.doesNotMatch(val,/^\s*javascript:/i,'index.html: javascript: URL');
 }
 for(const [name,css] of Object.entries(CSS_SOURCES())){
  assert.doesNotMatch(css,/@font-face|@import|font-display|expression\(/i,name+': web font, import or expression');
  assert.doesNotMatch(css,/url\(\s*['"]?\s*(?:https?:)?\/\//i,name+': external url()');
 }
 for(const f of ['app.js','journey-ui.js','experience.js','teaching.js','theme.js','guidance-core.js','prayer-output.js']){
  const s=read(f);
  assert.doesNotMatch(s,/\sstyle\s*=\s*(?:\\?["'`])/,f+': a style attribute in markup');
  assert.doesNotMatch(s,/setAttribute\(\s*['"`]style['"`]|\.style\.cssText|<style\b|createElement\(\s*['"`](?:style|script)['"`]/,f+': inline style or script creation');
  assert.doesNotMatch(s,/\beval\(|new Function\(|fonts\.googleapis|@font-face/,f+': eval, Function or web font');
  assert.doesNotMatch(s,/\son(?:click|load|error|input|change|submit|focus|blur|key\w+|mouse\w+|touch\w+|pointer\w+)\s*=\s*\\?["'`]/i,f+': inline event handler in markup');
 }
 for(const v of VARIANTS){
  const {html,dom}=pray(v);
  assert.doesNotMatch(html,/<style\b/i,v+': <style> in the Pray markup');
  for(const n of els(dom)){assert.ok(!('style' in n.attrs),v+': style attribute on <'+n.tag+'>');for(const a of Object.keys(n.attrs))assert.doesNotMatch(a,/^on/,v+': inline handler '+a);}
 }
});

const ESV_PHRASES=['not my will but yours be done','search me o god','my soul is very sorrowful','do not be conformed to this world','present your bodies as a living sacrifice','by grace you have been saved through faith','the wages of sin is death','if the son sets you free','do not be anxious about anything','if any of you lacks wisdom','without counsel plans fail','the fruit of the spirit is love','a man after my heart','pouring out my soul before the lord','daniel resolved that he would not defile','had set his heart to study the law','four things on earth are small','trust in the lord with all your heart','i know the plans i have for you','i can do all things through him','be still and know that i am god','come to me all who labor','for god so loved the world','your word is a lamp to my feet','seek first the kingdom of god','fear not for i am with you','pray without ceasing'];
test('no_quoted_scripture: the Pray screen links to passages but quotes no verse text (I14)',()=>{
 const book=/(?:[1-3]\s)?(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|Song|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s+\d+:\d+/;
 const quoted=new RegExp('[“"‘][^”"’]{12,}[”"’]\\s*[(\\-,]?\\s*'+book.source+'|'+book.source+'[^“"‘]{0,6}[“"‘]');
 const docs=VARIANTS.map(v=>[v,pray(v).dom]).concat([['index.html',index()]]);
 for(const [name,dom] of docs){
  for(const n of els(dom)){
   assert.ok(!['blockquote','q','cite'].includes(n.tag),name+': <'+n.tag+'> on the Pray screen');
   for(const c of cls(n))assert.doesNotMatch(c,/verse-text|scripture-text|scripture-quote|bible-quote|verse-banner|daily-verse/,name+': class '+c);
  }
  const text=visibleText(dom,a=>cls(a).includes('verse-link'));
  const plain=text.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu,' ').replace(/\s+/g,' ');
  for(const p of ESV_PHRASES)assert.ok(!plain.includes(p),name+': quotes Scripture ("'+p+'")');
  assert.doesNotMatch(text,quoted,name+': a quotation attributed to a Bible reference');
 }
});

test('verbatim_invariant_lines: the principle lines and the consent sentence stay word for word; consent and the acknowledgement render unticked; the Soul belonging choice keeps its meaning (I15, I3, I4)',()=>{
 const ok=collector();
 for(const v of VARIANTS){
  const {dom}=pray(v);
  const decision=byId(dom,'guide-decision');
  if(ok(decision,v+': #guide-decision missing')){const dt=visibleText(decision);for(const line of ['The next step I choose','These are considerations, not a divine verdict.'])ok(dt.includes(line),v+': #guide-decision lost "'+line+'"');}
  const consent=byId(dom,'guidance-consent');
  if(ok(consent,v+': #guidance-consent missing')){
   ok(consent.attrs.type==='checkbox',v+': #guidance-consent is not a checkbox');ok(!('checked' in consent.attrs),v+': consent is ticked by default');
   const label=up(consent).find(a=>a.tag==='label')||els(dom).find(n=>n.tag==='label'&&n.attrs.for==='guidance-consent');
   if(ok(label,v+': the consent checkbox has no label (wrapping, or for="guidance-consent")'))ok(ownText(label).includes(CONSENT),v+': the consent sentence is not verbatim in its label: "'+ownText(label)+'"');
   ok(!inDetailsOrHidden(up(consent)),v+': the consent checkbox is hidden or inside a closed details');
  }
  const belonging=els(dom).find(n=>n.tag==='select'&&n.attrs['data-field']==='belonging');
  if(ok(belonging,v+': Soul belonging choice missing')){
   ok(up(belonging).some(a=>a.attrs.id==='reflection-S'),v+': belonging choice left the Soul area');
   ok(!inDetailsOrHidden(up(belonging)),v+': belonging choice is hidden');
   const opts=els(belonging).filter(n=>n.tag==='option');
   ok(opts[0]?.attrs.value===''&&norm(textOf(opts[0])).length>0,v+': the first belonging option must be the no-assumption default (value "")');
   ok(opts.some(o=>o.attrs.value==='private'),v+': the "private" belonging option is missing');
   ok(!opts.some(o=>'selected' in o.attrs&&o.attrs.value!==''),v+': a belonging option other than the default renders selected');
  }
 }
 const confirm=byId(pray('guided').dom,'guidance-confirm');
 if(ok(confirm,'guided: #guidance-confirm missing'))ok(!('checked' in confirm.attrs),'guided: the understanding acknowledgement is ticked without the person');
 const j=read('journey-ui.js');for(const line of ['Local starting prayer','Nothing was sent',CONSENT])ok(j.includes(line),'journey-ui.js lost "'+line+'"');
 ok.done('verbatim lines changed');
});

test('core_questions_unchanged: the five core questions keep today\'s on-screen wording (A14)',()=>{
 const {dom}=pray('blank');
 for(const k of KEYS){const q=byId(dom,'question-'+k);assert.ok(q,'#question-'+k+' missing');assert.equal(norm(textOf(q)),QUESTIONS[k],'the '+NAMES[k]+' question changed');}
});

test('teaching_text_unchanged: the intro, guardrails and summary keep their words; only the example-prayer fold markup may change (A12)',()=>{
 for(const [k,want] of Object.entries(TEACHING_TEXT)){
  const dom=parse(TE.content(k)),got=wordsOf(dom,a=>a.tag==='summary');
  assert.equal(got,want,'teaching.js "'+k+'" text changed');
 }
 const intro=parse(TE.content('intro')),fold=els(intro).find(n=>n.tag==='details');
 assert.ok(fold&&!('open' in fold.attrs),'the intro needs a closed <details> fold for the two example prayers');
 assert.equal(norm(textOf(els(fold).find(n=>n.tag==='summary')||{children:[]})),'Show two short example prayers','the fold summary must read "Show two short example prayers"');
 const ft=wordsOf(fold);assert.ok(ft.includes('During conflict')&&ft.includes('Afterwards - thanksgiving'),'both example prayers must sit inside the fold');
});

test('tokens_contrast: ink and every text colour reach 7:1 on every pale surface, accents 4.5:1, lines and focus 3:1, with the effective cascade (I12, A17)',()=>{
 const {map,resolve}=tokens(),hexTokens=Object.fromEntries(Object.keys(map).map(k=>[k,resolve(map[k])]).filter(([,h])=>h));
 for(const k of ['ink','muted','line','action','focus','paper','surface'])assert.ok(hexTokens[k],'token --'+k+' is missing or not a hex colour');
 const pale=Object.entries(hexTokens).filter(([,h])=>luminance(h)>=0.6);
 assert.ok(pale.length>=2,'no pale surfaces found');
 const fails=[];
 const need=(fg,bg,min,what)=>{const r=contrast(fg,bg);if(r+1e-9<min)fails.push(`${what}: ${r.toFixed(2)}:1 < ${min}:1`);};
 const accentNames=Object.keys(hexTokens).filter(t=>t==='action'||t==='focus'||/accent|attention|^area-|gilt|gold/i.test(t));
 const accentHex=new Set(accentNames.map(t=>hexTokens[t]));
 const lineTokens=Object.entries(hexTokens).filter(([t])=>t==='line'||/gilt|gold|rule|hairline|border/i.test(t));
 const areas=areaColours(resolve);
 const areaAccents=Object.values(areas).map(a=>a['area-accent']).filter(Boolean);
 for(const h of areaAccents)accentHex.add(h);
 /* Text colours: the named text tokens, plus every value a `color:` declaration uses. */
 const textColours=new Map();
 for(const [t,h] of Object.entries(hexTokens))if(/^(ink|muted)$|helper|hint|^text/i.test(t))textColours.set(h,'--'+t);
 /* The last `color:` declared for the same selector in the same media context is the live one. */
 const declared=new Map();
 for(const r of allRules()){
  if(printOrForced(r))continue;
  for(const m of r.body.matchAll(/(?:^|[;{\s])color\s*:\s*([^;!]+)/g))declared.set(r.media.join(' | ')+' :: '+norm(r.sel),{r,raw:m[1].trim()});
 }
 for(const {r,raw} of declared.values()){
  {
   if(/^(inherit|currentcolor|transparent|initial|unset|revert)$/i.test(raw))continue;
   if(/^var\(\s*--area-accent\s*\)$/.test(raw)){if(!areaAccents.length)fails.push(r.file+': '+r.sel+' uses --area-accent but no area declares one');continue;}
   const h=resolve(raw);
   if(!h){fails.push(r.file+': '+r.sel+' uses a text colour this test cannot resolve ("'+raw+'"); use a hex token');continue;}
   if(!textColours.has(h))textColours.set(h,r.file+': '+r.sel+' color:'+raw);
  }
 }
 for(const [h,what] of textColours){
  if(luminance(h)>=0.6){for(const bg of ['action','ink'])need(h,hexTokens[bg],4.5,what+' (pale text) on --'+bg);continue;}
  const min=accentHex.has(h)?4.5:7;
  for(const [name,bg] of pale)need(h,bg,min,what+(min===7?' (text)':' (accent as text)')+' on --'+name);
 }
 for(const [name,bg] of pale){
  for(const [t,h] of lineTokens)need(h,bg,3,'--'+t+' (line) on --'+name);
  need(hexTokens.focus,bg,3,'--focus (indicator) on --'+name);
  for(const t of accentNames)if(luminance(hexTokens[t])<0.6)need(hexTokens[t],bg,4.5,'--'+t+' (accent) on --'+name);
 }
 need(hexTokens.surface,hexTokens.action,4.5,'--surface text on --action');
 assert.deepEqual(Object.keys(areas).sort(),[...KEYS].sort(),'each area needs an --area-accent colour (a rule naming data-area=K or reflection-K); found '+Object.keys(areas).join(', '));
 for(const [k,a] of Object.entries(areas)){
  for(const bg of ['paper','surface'])need(a['area-accent'],hexTokens[bg],4.5,k+' accent on --'+bg);
  if(a['area-tint'])need(a['area-accent'],a['area-tint'],4.5,k+' accent on its tint');
 }
 const gilt=Object.keys(hexTokens).filter(k=>/gilt|gold/i.test(k)).map(k=>hexTokens[k]);
 if(gilt.includes(hexTokens.line))fails.push('--line is a gilt colour; every hairline on prayer and AI containers would be gilt (I18)');
 assert.deepEqual(fails,[],'contrast below the floor:\n'+fails.join('\n'));
});

test('copy_rules (advisory only; not in the approved spec, so it never fails): "·" separators, lower-cased label placeholders and text-transform in the Pray copy',t=>{
 const notes=[];
 for(const v of VARIANTS){
  const {dom}=pray(v);
  for(const n of els(dom)){
   let words=null;
   if(n.tag==='label'||n.tag==='legend')words=ownText(n);
   else if(n.tag==='summary'||n.tag==='option')words=norm(textOf(n));
   else if(n.tag==='button'&&!cls(n).includes('verse-link'))words=norm(textOf(n));
   if(words!==null&&words.includes('·'))notes.push(v+': <'+n.tag+'> "'+words+'"');
   for(const a of ['placeholder','aria-label','title'])if(n.attrs[a]!==undefined&&n.attrs[a].includes('·'))notes.push(v+': '+a+' "'+n.attrs[a]+'"');
   if(n.attrs.placeholder!==undefined&&/w\.h\.e\.m\.s\.|christ-centred/.test(n.attrs.placeholder))notes.push(v+': placeholder "'+n.attrs.placeholder+'"');
  }
 }
 for(const [name,css] of Object.entries(CSS_SOURCES()))if(/text-transform\s*:/i.test(css))notes.push(name+': text-transform');
 t.diagnostic(notes.length?'copy_rules advisory: '+notes.length+' item(s), e.g. '+notes.slice(0,4).join(' | '):'copy_rules advisory: nothing to report');
});

test('language_rules: lang="en-GB"; only the brand and the W.H.E.M.S. letters are protected from browser translation; the rest stays translatable (A9)',()=>{
 const ok=collector(),idx=index();
 const html=els(idx).find(n=>n.tag==='html'),body=els(idx).find(n=>n.tag==='body');
 ok(html?.attrs.lang==='en-GB','<html lang> is "'+html?.attrs.lang+'", not "en-GB"');
 for(const n of [html,body])if(n){ok(n.attrs.translate!=='no','<'+n.tag+'> carries translate="no"');ok(!cls(n).includes('notranslate'),'<'+n.tag+'> carries class "notranslate"');}
 ok(!els(idx).some(n=>n.tag==='meta'&&/notranslate/i.test(n.attrs.content||'')),'a notranslate meta blocks translation of the whole page');
 const guarded=n=>up(n).some(a=>a.attrs.translate==='no');
 const brand=els(idx).find(n=>cls(n).includes('brand'));
 if(ok(brand,'header brand missing')){
  const brandText=textNodes(brand).filter(t=>norm(t.text));
  ok(brandText.some(t=>t.text.includes('Wholehearted')),'brand name missing');
  for(const t of brandText)ok(guarded(t),'brand text "'+norm(t.text)+'" lacks translate="no"');
 }
 for(const t of textNodes(body||idx))if(t.text.includes('W.H.E.M.S.')&&!up(t).some(a=>a.tag==='noscript'))ok(guarded(t),'index.html: "W.H.E.M.S." in "'+norm(t.text)+'" lacks translate="no"');
 const teaching=a=>['prayer-introduction','guardrails','one-line-summary'].includes(a.attrs.id);
 /* Every translate="no" element must be the brand (or inside it), an svg, exactly "W.H.E.M.S." or one area letter. */
 const allowed=n=>n.tag==='svg'||cls(n).includes('brand')||up(n).slice(1).some(a=>cls(a).includes('brand'))||norm(textOf(n))==='W.H.E.M.S.'||KEYS.includes(norm(textOf(n)));
 for(const [name,dom] of [['index.html',idx],...VARIANTS.map(v=>[v,pray(v).dom])]){
  for(const n of els(dom))if(n.attrs.translate==='no')ok(allowed(n),name+': translate="no" on <'+n.tag+'> blocks translation of "'+norm(textOf(n)).slice(0,60)+'"');
  for(const n of els(dom))ok(!cls(n).includes('notranslate'),name+': class "notranslate" on <'+n.tag+'>');
 }
 for(const v of VARIANTS){
  const {dom}=pray(v);
  for(const t of textNodes(dom))if(t.text.includes('W.H.E.M.S.')&&!up(t).some(a=>teaching(a)||['textarea','option','select'].includes(a.tag)))ok(guarded(t),v+': "W.H.E.M.S." in "'+norm(t.text)+'" lacks translate="no"');
  for(const k of KEYS){
   const area=byId(dom,'reflection-'+k),h=area&&els(area).find(n=>/^h[23]$/.test(n.tag));
   if(!ok(h,v+': area '+k+' heading missing'))continue;
   const letter=textNodes(h).find(t=>norm(t.text)===k);
   if(ok(letter,v+': area '+k+' heading lost its own letter element'))ok(guarded(letter),v+': the area letter '+k+' lacks translate="no"');
  }
 }
 ok.done('language rule breaches');
});

/* Latin cross: one vertical stem, one shorter crossbar above the stem's middle; straight lines only.
   Filled rectangles (rect elements or closed four-corner sub-paths) count by their centreline. */
function crossShape(svg){
 const shapes=[];let curves=false;
 const nums=s=>(s||'').trim().split(/[\s,]+/).filter(Boolean).map(Number);
 for(const n of els(svg)){
  const num=k=>parseFloat(n.attrs[k]||'0');
  if(n.tag==='line')shapes.push({pts:[[num('x1'),num('y1')],[num('x2'),num('y2')]],closed:false});
  else if(n.tag==='rect'){const x=num('x'),y=num('y'),w=num('width'),h=num('height');shapes.push({pts:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],closed:true});}
  else if(n.tag==='polyline'||n.tag==='polygon'){const p=nums(n.attrs.points),pts=[];for(let i=0;i+1<p.length;i+=2)pts.push([p[i],p[i+1]]);shapes.push({pts,closed:n.tag==='polygon'});}
  else if(n.tag==='path'){
   const tok=(n.attrs.d||'').match(/[a-zA-Z]|-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/g)||[];
   let i=0,cmd='',x=0,y=0,sx=0,sy=0,sub=null;const next=()=>parseFloat(tok[i++]);
   const flush=closed=>{if(sub&&sub.length>1)shapes.push({pts:sub,closed});sub=null;};
   while(i<tok.length){
    if(/[a-zA-Z]/.test(tok[i]))cmd=tok[i++];
    const rel=cmd===cmd.toLowerCase(),CMD=cmd.toUpperCase();
    if(CMD==='M'){flush(false);x=(rel?x:0)+next();y=(rel?y:0)+next();sx=x;sy=y;sub=[[x,y]];cmd=rel?'l':'L';}
    else if(CMD==='L'){x=(rel?x:0)+next();y=(rel?y:0)+next();sub.push([x,y]);}
    else if(CMD==='H'){x=(rel?x:0)+next();sub.push([x,y]);}
    else if(CMD==='V'){y=(rel?y:0)+next();sub.push([x,y]);}
    else if(CMD==='Z'){x=sx;y=sy;flush(true);sub=[[x,y]];}
    else{curves=true;break;}
   }
   flush(false);
  }
 }
 if(curves)return 'uses curves or arcs; draw the cross with straight segments';
 const same=(a,b)=>Math.abs(a[0]-b[0])<0.01&&Math.abs(a[1]-b[1])<0.01;
 const segs=[],outlines=[];
 for(const s of shapes){
  let pts=s.pts.filter((p,i)=>i===0||!same(p,s.pts[i-1]));
  if(s.closed&&pts.length>1&&same(pts[0],pts[pts.length-1]))pts=pts.slice(0,-1);
  if(pts.length<2)continue;
  const xs=[...new Set(pts.map(p=>p[0].toFixed(2)))],ys=[...new Set(pts.map(p=>p[1].toFixed(2)))];
  if(s.closed&&pts.length===4&&xs.length===2&&ys.length===2){
   const x0=Math.min(...pts.map(p=>p[0])),x1=Math.max(...pts.map(p=>p[0])),y0=Math.min(...pts.map(p=>p[1])),y1=Math.max(...pts.map(p=>p[1]));
   if(y1-y0>=x1-x0)segs.push([[(x0+x1)/2,y0],[(x0+x1)/2,y1]]);else segs.push([[x0,(y0+y1)/2],[x1,(y0+y1)/2]]);
   continue;
  }
  for(let i=1;i<pts.length;i++)segs.push([pts[i-1],pts[i]]);
  if(s.closed){segs.push([pts[pts.length-1],pts[0]]);if(pts.length===12)outlines.push(pts);}
 }
 if(!segs.length)return 'draws nothing';
 if(segs.some(([a,b])=>Math.abs(a[0]-b[0])>0.01&&Math.abs(a[1]-b[1])>0.01))return 'has a diagonal stroke';
 const xs=segs.flat().map(p=>p[0]),ys=segs.flat().map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),W=maxX-minX,H=maxY-minY;
 if(!(H>W))return 'is not taller than it is wide';
 let barY,stemX;
 if(outlines.length===1&&shapes.length===1){
  const vAtLeft=segs.filter(([a,b])=>Math.abs(a[0]-minX)<0.01&&Math.abs(b[0]-minX)<0.01);
  const hAtTop=segs.filter(([a,b])=>Math.abs(a[1]-minY)<0.01&&Math.abs(b[1]-minY)<0.01);
  if(vAtLeft.length!==1||hAtTop.length!==1)return 'outline is not a single-bar cross';
  barY=(vAtLeft[0][0][1]+vAtLeft[0][1][1])/2;stemX=(hAtTop[0][0][0]+hAtTop[0][1][0])/2;
 }else{
  const len=([a,b])=>Math.hypot(a[0]-b[0],a[1]-b[1]);
  const v=segs.filter(([a,b])=>Math.abs(a[0]-b[0])<=0.01),h=segs.filter(([a,b])=>Math.abs(a[1]-b[1])<=0.01);
  if(!v.length||!h.length)return 'needs both a stem and a crossbar';
  const stem=v.reduce((p,c)=>len(c)>len(p)?c:p),bar=h.reduce((p,c)=>len(c)>len(p)?c:p);
  if(!(len(stem)>len(bar)))return 'crossbar is not shorter than the stem';
  if(new Set(h.filter(s=>len(s)>=0.5*len(bar)).map(s=>s[0][1].toFixed(2))).size!==1)return 'has more than one crossbar';
  if(new Set(v.filter(s=>len(s)>=0.5*len(stem)).map(s=>s[0][0].toFixed(2))).size!==1)return 'has more than one stem';
  barY=bar[0][1];stemX=stem[0][0];
 }
 if(!(barY>minY+0.1*H))return 'crossbar sits at the top (a tau cross, not a Latin cross)';
 if(!(barY<minY+H/2))return 'crossbar is not above the middle of the stem';
 if(!(stemX>minX+0.15*W&&stemX<maxX-0.15*W))return 'crossbar does not reach both sides of the stem';
 return null;
}
const CROSS_GLYPHS=/[†‡✝✞✟✙✚✛✜✠☦☨☩☧⳩\u{1F546}-\u{1F548}]/u;
const decodeCss=s=>s.replace(/\\([0-9a-f]{1,6})\s?/gi,(m,h)=>String.fromCodePoint(parseInt(h,16)));
const COLOUR_WORDS=/\b(purple|violet|gold|golden|gilt|gilded|white|red|scarlet|crimson|green|blue|black)\b/i;
const MEANING_WORDS=/\b(means|meaning|signif\w*|symboli\w+|symbol of|represents?|stands for|penitence|penance|royalty|kingship|glory|purity|holiness|the blood|sacrifice|liturgical|sacred colour)\b/i;
test('look_rules: the brand is an empty Latin cross in inline SVG, no "w." monogram, no cross or gilt on prayer or AI text, no colour given a religious meaning (I18, A8)',()=>{
 const ok=collector(),idx=index(),brand=els(idx).find(n=>cls(n).includes('brand'));
 ok(!textNodes(idx).some(t=>norm(t.text)==='w.'),'the "w." monogram is still in index.html');
 if(ok(brand,'header brand missing')){
  ok(!els(brand).some(n=>cls(n).includes('monogram')&&norm(textOf(n))),'a text monogram is still in the brand');
  const svgs=els(brand).filter(n=>n.tag==='svg');
  if(ok(svgs.length===1,'the brand needs exactly one inline <svg> mark; found '+svgs.length)){
   const svg=svgs[0];
   ok(svg.attrs['aria-hidden']==='true','the brand cross must be aria-hidden');
   ok(svg.attrs.viewbox,'the brand cross needs a viewBox so it can scale with text');
   for(const n of [svg,...els(svg)]){
    ok(!('style' in n.attrs),'SVG style attribute on <'+n.tag+'>');
    ok(!['style','script','image','text','use','foreignobject','circle','ellipse'].includes(n.tag),'the brand mark must be a plain cross; found <'+n.tag+'>');
   }
   const shape=crossShape(svg);ok(shape===null,'the brand SVG is not an empty Latin cross: it '+shape);
  }
 }
 const containerIds=['guide-prayers','guide-understanding-slot','guide-understanding','guide-consent','guide-options','prayer-flow-status','ai-state','three-prayer-forms'];
 const containerClasses=['prayer-form-block','final-prayers','interpretation','consent-box','context-focus','guidance-source','prayer-flow-status','prayer-form-feedback','decision-option','reply-question'];
 const aiOrPrayer=a=>containerIds.includes(a.attrs.id)||/^(question|reply-label)-[WHEMS]$/.test(a.attrs.id||'')||'data-context-focus' in a.attrs||'data-context-followup' in a.attrs||'data-context-references' in a.attrs||cls(a).some(c=>containerClasses.includes(c));
 const insideClasses=new Set(),insideIds=new Set();
 for(const v of VARIANTS){
  const {dom}=pray(v);
  for(const n of els(dom)){
   if(!up(n).some(aiOrPrayer))continue;
   for(const c of cls(n))insideClasses.add(c);if(n.attrs.id)insideIds.add(n.attrs.id);
   ok(!['svg','img','picture'].includes(n.tag),v+': <'+n.tag+'> inside a prayer or AI container');
   for(const c of cls(n))ok(!/cross|gilt|gold|ornament|crucifix|flourish/i.test(c),v+': class '+c+' inside a prayer or AI container');
  }
  for(const t of textNodes(dom))ok(!(CROSS_GLYPHS.test(t.text)&&up(t).some(aiOrPrayer)),v+': cross glyph inside a prayer or AI container');
 }
 const {map,resolve}=tokens(),gilt=Object.keys(map).filter(k=>/gilt|gold/i.test(k)),giltHex=gilt.map(k=>resolve(map[k])).filter(Boolean);
 const target=/#guide-prayers|\.final-prayers|\.prayer-form-block|data-prayer-form|#prayer-flow-status|\.prayer-flow-status|\.prayer-form-feedback|#guide-understanding|\.interpretation|#guide-consent|\.consent-box|\.context-focus|\.guidance-source|#guide-options|\.decision-option|#ai-state|#question-[WHEMS]|\.reply-question|data-context-followup|data-context-references|#reply-label-[WHEMS]|data-context-focus/;
 const mentionsInside=sel=>[...insideClasses].some(c=>sel.includes('.'+c))||[...insideIds].some(i=>sel.includes('#'+i));
 for(const r of allRules()){
  if(printOrForced(r))continue;
  const sel=r.sel,body=decodeCss(r.body);
  ok(!(/content\s*:/.test(body)&&(CROSS_GLYPHS.test(body)||/content\s*:[^;]*url\(/.test(body))),r.file+': '+sel+' draws a symbol with CSS content');
  if(!target.test(sel)&&!mentionsInside(sel))continue;
  ok(!(gilt.some(k=>body.includes('--'+k))||giltHex.some(h=>body.toLowerCase().includes(h))),r.file+': '+sel+' uses gilt');
  ok(!/(?:background(?:-image)?|mask(?:-image)?|border-image|list-style(?:-image)?)\s*:[^;]*url\(/i.test(body),r.file+': '+sel+' draws an image');
 }
 if(giltHex.includes(resolve(map.line)))ok(false,'--line is a gilt colour; hairlines on prayer and AI containers would be gilt');
 const copy=[['Pray (rendered)',VARIANTS.map(v=>visibleText(pray(v).dom)).join(' ')],...['index.html','app.js','journey-ui.js','experience.js','theme.js','styles.css','experience.css','README.md'].map(f=>[f,read(f)])];
 for(const [name,text] of copy)for(const sentence of text.split(/(?<=[.!?;])\s+|\n/))ok(!(COLOUR_WORDS.test(sentence)&&MEANING_WORDS.test(sentence)&&!/\b(no|not|never|without)\b/i.test(sentence)),name+': gives a colour a religious meaning: "'+norm(sentence).slice(0,140)+'"');
 ok.done('look rule breaches');
});

function core(issue){
 // The issue without a leading question word and pronoun, so "whether I should ..." also counts as containing it.
 const words=issue.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu,' ').split(/\s+/).filter(Boolean);
 if(/^(should|can|could|would|will|shall|may|might|must|do|does|did|is|are|am|was|were|have|has|how|what|when|where|why|who|which)$/.test(words[0])){words.shift();if(/^(i|we|you|he|she|they|it|my|our)$/.test(words[0]))words.shift();}
 return words.join(' ');
}
const flat=s=>' '+s.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu,' ').replace(/\s+/g,' ').trim()+' ';
const BROKEN_GRAMMAR=[
 [/\b(?:bring|with|for|about)\s+(?:should|can|could|would|will|shall|may|might|must|do|does|did|is|are|am|how|what|when|where|why|who|which)\s+(?:i|we|you|he|she|they)\b/i,'pastes the question into the clause ("bring should I ...")'],
 [/(^|[^A-Za-z'’])i([^A-Za-z'’]|$)/,'has a lower-case standalone "i"'],
 [/\?\s+[a-z]|\.\s+[a-z]/,'breaks a sentence after "?" or "."']];
function fixture(issue,voice='personal'){const d=J.blank('mixed','2026-10-09T01:00:00Z','quick-fixture');d.journey.issue=issue;d.journey.voice=voice;return d;}
function grammar(ok,text,tag){for(const [re,why] of BROKEN_GRAMMAR)ok(!re.test(text),tag+' '+why+': '+text.replace(/\s+/g,' ').slice(0,160));}
test('quick_prayer_wording: the local prayers name the issue grammatically in the sentence and the W.H.E.M.S. form, for a question-shaped issue too (I17, A15)',()=>{
 const ok=collector();
 for(const voice of ['personal','community'])for(const issue of [QUESTION_ISSUE,STATEMENT_ISSUE]){
  const f=G.local(fixture(issue,voice)),tag=voice+' / "'+issue+'"';
  ok(flat(f.sentence).includes(' '+core(issue)+' '),tag+': the one-sentence prayer does not contain the issue: '+f.sentence);
  ok(flat(f.whems).includes(' '+core(issue)+' '),tag+': the W.H.E.M.S. prayer does not contain the issue');
  ok(/^Father,/.test(f.sentence),tag+': the sentence must still address the Father');
  grammar(ok,f.sentence,tag+': the sentence');
  for(const para of f.whems.split(/\n\s*\n/))grammar(ok,para,tag+': a W.H.E.M.S. paragraph');
  for(const k of KEYS)ok(f.whems.includes(k+' - '+NAMES[k]+'\n'),tag+': W.H.E.M.S. heading '+k+' missing');
  ok(f.extended.includes(issue),tag+': the extended prayer must still contain the issue');
  const words=f.extended.split(/\s+/).length;ok(words>=450&&words<=900,tag+': extended prayer length '+words);
  ok(/Local/.test(f.origin),tag+': origin must say Local');
  ok(!/you are controlling|daughter is saved|daughter is depressed|God says|you have answered this/.test(f.extended),tag+': judgement wording');
  if(voice==='community')ok(/We come/.test(f.extended)&&/ourselves/.test(f.extended)&&!f.extended.includes('ourself')&&!f.extended.includes('we are saved'),tag+': community voice broken');
  else ok(/Search my heart/.test(f.extended),tag+': personal voice broken');
 }
 const d=fixture(QUESTION_ISSUE);d.areas.W.thank=true;d.areas.W.thankNote='willingness to listen';d.areas.E.ask=true;d.areas.E.askNote='patience';d.areas.H.askNote='HIDDEN PRIVATE NOTE';
 const f=G.local(d);
 ok(!JSON.stringify(f).includes('HIDDEN'),'a deselected note leaked into a prayer');
 ok(f.sentence.includes('willingness to listen')&&f.sentence.includes('patience'),'chosen thanksgiving and request must stay in the sentence');
 ok(flat(f.sentence).includes(' '+core(QUESTION_ISSUE)+' '),'with notes chosen, the sentence must still contain the issue: '+f.sentence);
 ok(flat(f.whems).includes(' '+core(QUESTION_ISSUE)+' '),'with notes chosen, the W.H.E.M.S. prayer must still contain the issue');
 grammar(ok,f.sentence,'with notes chosen, the sentence');
 for(const para of f.whems.split(/\n\s*\n/))grammar(ok,para,'with notes chosen, a W.H.E.M.S. paragraph');
 let valid=false;try{valid=!!G.validatePrayers(f).extended;}catch(e){}
 ok(valid,'the local prayers must still pass the AI-format validator');
 ok.done('quick prayer wording breaches');
});
