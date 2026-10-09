"""Simple-path (Lamp Path) phone checks for the Pray screen redesign,
doc/Feature/2026-10-09-pray-ui-redesign.md (including Amendment 1). Each check name is the id that
the spec's acceptance criteria and invariants cite; one PASS, FAIL, ERROR or SKIP line is printed per
check and the script exits non-zero when any check fails or when no check ran.

HTTP mode (default) serves public/ from a small local server that sends the exact response
headers in vercel.json, so the production Content-Security-Policy applies. DOM mode injects
the built assets for environments that prohibit navigation; it cannot check the CSP or the
storage key list. AI responses are labelled test fixtures; every request that would leave this
machine is aborted, so no model or Scripture service is ever called. Chromium cannot emulate
notch insets or an on-screen keyboard: simulated_safe_area injects --inset-l/--inset-r/--inset-b
and the keyboard checks replace visualViewport with an explicit geometry fixture. Neither is a
physical-device result.

Run `node build.cjs` first; the script refuses a stale public/. Environment: EVIDENCE_DIR
(default <repo>/evidence; keep it outside the repository), BROWSER_MODE=http|dom,
TEST_BROWSER=chromium|webkit, CHROMIUM_PATH, SIMPLE_PATH_CHECKS (comma-separated subset of
check names), SIMPLE_PATH_SIZES (comma-separated WxH list for the per-size behaviour checks).
"""
import json, os, re, sys, threading, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
OUT=Path(os.environ.get('EVIDENCE_DIR', str(ROOT/'evidence')))/'simple-path'
OUT.mkdir(parents=True,exist_ok=True)
MODE=os.environ.get('BROWSER_MODE','http')
ENGINE=os.environ.get('TEST_BROWSER','chromium')
ONLY={x.strip() for x in os.environ.get('SIMPLE_PATH_CHECKS','').split(',') if x.strip()}

def parse_sizes(text):
  out=[]
  for part in text.split(','):
    m=re.fullmatch(r'\s*(\d+)\s*x\s*(\d+)\s*',part)
    if not m: sys.exit('SIMPLE_PATH_SIZES must be WxH pairs, for example 320x568,844x390; got '+repr(part))
    out.append((int(m.group(1)),int(m.group(2))))
  return out
PORTRAIT=[(320,568),(360,740),(360,800),(375,667),(375,812),(390,844),(393,852),(402,874),(412,915),(430,932),(440,956)]
LANDSCAPE=[(h,w) for w,h in PORTRAIT]
TABLETS=[(768,1024),(1024,768)]
# The behaviour checks run at these sizes (three portrait and their landscape pairs) unless overridden.
SIMPLE_PATH_SIZES=parse_sizes(os.environ['SIMPLE_PATH_SIZES']) if os.environ.get('SIMPLE_PATH_SIZES') else [(320,568),(390,844),(440,956),(568,320),(844,390),(956,440)]
SIZES=['Standard','Larger','Largest']
KEYS=['W','H','E','M','S']
NAMES={'W':'Will','H':'Heart','E':'Emotions','M':'Mind','S':'Soul'}
NEXT={'W':'H','H':'E','E':'M','M':'S'}
QUICK='Pray with what I have written'
DEEPER='Go deeper in each area'
SAVE_PROMISE='Your words stay only on this page until you tap Save.'
SAFETY='When to get other help as well'
JOURNAL_KEY='wholehearted-journal-v3'
ISSUE='Should I talk to my daughter or pray while her research learning curve is steep?'
SCRIPTS={'Chinese':'我应该和女儿谈谈，还是先为她祷告？','Malay':'Patutkah saya bercakap dengan anak perempuan saya atau berdoa dahulu?','Tamil':'நான் என் மகளிடம் பேச வேண்டுமா அல்லது முதலில் ஜெபிக்க வேண்டுமா?'}
# Section 23 of doc/background.MD: ten topics, each matched by a word family to a distinct list item
# (plain-English rewording is allowed; one item may name two topics joined by "or" or "and").
SAFETY_TOPICS={'immediate danger':r'danger|immediate','self-harm or harm to another person':r'harm|hurt|suicid','abuse':r'abus','coercion':r'coerc|forc|pressur|controll',
 'serious medical symptoms':r'medic|symptom|health|illness|doctor','legal deadlines':r'legal|\blaw\b|court|deadline','large or irreversible financial consequences':r'financ|money|debt|loan',
 'safeguarding children or vulnerable adults':r'safeguard|child|vulnerable','emergency services':r'emergenc|ambulance|police|\b99[59]\b|\b911\b','competent professional advice':r'professional|expert|trained|qualified|counsel'}

def vercel_headers():
  cfg=json.loads((ROOT/'vercel.json').read_text())
  out=[(h['key'],h['value']) for rule in cfg.get('headers',[]) if rule.get('source')=='/(.*)' for h in rule.get('headers',[])]
  assert any(k=='Content-Security-Policy' for k,_ in out),'vercel.json no longer sets a CSP for every path'
  return out
HEADERS=vercel_headers()
CSP=dict(HEADERS)['Content-Security-Policy']

def fresh_build():
  """public/ must be the build of the current sources; a stale folder would test old assets."""
  src=(ROOT/'build.cjs').read_text()
  m=re.search(r"const assets=\[([^\]]*)\]",src)
  assets=re.findall(r"'([^']+)'",m.group(1)) if m else []
  theme=re.search(r"const css=`([^`]*)`",(ROOT/'theme.js').read_text())
  if not assets or not theme: sys.exit('build.cjs or theme.js changed shape; the freshness check cannot read the asset list')
  stale=[]
  for f in assets:
    want=(theme.group(1)+'\n').encode()+(ROOT/f).read_bytes() if f=='styles.css' else (ROOT/f).read_bytes()
    if not (PUBLIC/f).exists() or (PUBLIC/f).read_bytes()!=want: stale.append(f)
  if not (PUBLIC/'build-info.js').exists(): stale.append('build-info.js')
  if stale: sys.exit('public/ is missing or stale ('+', '.join(stale)+'): run `node build.cjs` first.')

class VercelHeaders(SimpleHTTPRequestHandler):
  """Static server for public/ that adds the vercel.json headers to every response."""
  extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.html':'text/html; charset=utf-8','.json':'application/json'}
  def __init__(self,*a,**k): super().__init__(*a,directory=str(PUBLIC),**k)
  def end_headers(self):
    for k,v in HEADERS: self.send_header(k,v)
    self.send_header('Cache-Control','no-store')
    super().end_headers()
  def log_message(self,*a): pass

class QuietServer(ThreadingHTTPServer):
  daemon_threads=True
  def handle_error(self,request,client_address): pass  # aborted navigations reset sockets; not a test result

# Runs before any page script: counts storage writes, records CSP violations and app-initiated scrolls.
INIT_JS=r'''(()=>{if(window.__sp)return;const sp=window.__sp={writes:0,sessionWrites:0,idb:0,beacons:0,csp:[],scrolls:[]};
try{const P=Storage.prototype,set=P.setItem,rem=P.removeItem,clr=P.clear;const which=s=>{try{return s===window.localStorage?'writes':'sessionWrites';}catch(e){return 'writes';}};
P.setItem=function(k,v){sp[which(this)]++;return set.call(this,k,v);};P.removeItem=function(k){sp[which(this)]++;return rem.call(this,k);};P.clear=function(){sp[which(this)]++;return clr.call(this);};}catch(e){}
try{const o=indexedDB.open.bind(indexedDB);indexedDB.open=(...a)=>{sp.idb++;return o(...a);};}catch(e){}
try{if(navigator.sendBeacon){const b=navigator.sendBeacon.bind(navigator);navigator.sendBeacon=(...a)=>{sp.beacons++;return b(...a);};}}catch(e){}
try{const to=window.scrollTo.bind(window),by=window.scrollBy.bind(window),sc=window.scroll.bind(window);sp.scrollTo=to;sp.scrollBy=by;
const rec=(fn,a)=>{const o=a[0]&&typeof a[0]==='object'?a[0]:{top:a[1],left:a[0]};sp.scrolls.push({fn,top:o.top,at:performance.now()});};
window.scrollTo=function(...a){rec('scrollTo',a);return to(...a);};window.scrollBy=function(...a){rec('scrollBy',a);return by(...a);};window.scroll=function(...a){rec('scroll',a);return sc(...a);};
const siv=Element.prototype.scrollIntoView;Element.prototype.scrollIntoView=function(...a){sp.scrolls.push({fn:'scrollIntoView',at:performance.now()});return siv.apply(this,a);};}catch(e){}
document.addEventListener('securitypolicyviolation',e=>sp.csp.push({directive:e.violatedDirective,blocked:e.blockedURI,source:e.sourceFile,line:e.lineNumber,sample:e.sample}));})();'''

# Shared helpers for page.evaluate bodies.
H=r'''const vis=e=>{if(!e)return false;if(e.checkVisibility&&!e.checkVisibility({visibilityProperty:true}))return false;const d=e.closest('details:not([open])');if(d&&!d.querySelector(':scope>summary')?.contains(e))return false;return e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden';};
const R=e=>{const r=e.getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height,right:r.right,bottom:r.bottom};};
const T=e=>(e?.innerText||e?.textContent||'').replace(/\s+/g,' ').trim();
const W=e=>{if(!e)return '';const c=e.cloneNode(true);c.querySelectorAll('[aria-hidden=true]').forEach(x=>x.remove());return (c.textContent||'').replace(/\s+/g,' ').trim();};
const before=(a,b)=>!!(a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING);
const name=e=>e?e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(typeof e.className==='string'&&e.className.trim()?'.'+e.className.trim().split(/\s+/).join('.'):'')+' "'+T(e).slice(0,40)+'"':'none';
const byText=(root,sel,re)=>[...(root||document).querySelectorAll(sel)].filter(e=>re.test(W(e)));
const gap=(a,b)=>Math.max(0,a.y-b.bottom,b.y-a.bottom);
const go=y=>{const to=(window.__sp&&window.__sp.scrollTo)||scrollTo.bind(window);to({top:y,left:0,behavior:'instant'});const want=Math.max(0,Math.min(y,document.documentElement.scrollHeight-innerHeight));if(Math.abs(scrollY-want)>=2)throw Error('scrolling to '+Math.round(y)+' landed at '+Math.round(scrollY)+' (smooth scrolling or a scroll lock)');return scrollY;};
const probe=v=>{const t=document.createElement('span');document.body.append(t);t.style.color=v;const c=getComputedStyle(t).color;t.remove();return c;};
const CROSS=/[†‡✝✞✟✙✚✛✜✠☦☨☩☧⳩\u{1F546}-\u{1F548}]/u;
'''
def js(body): return '(arg)=>{'+H+body+'}'

def guidance_fixture(data):
  """Labelled AI fixtures (never model output)."""
  if data.get('action')=='reflect':
    return {'result':{'summary':'TEST FIXTURE: You are considering how to support your daughter.','statedFacts':['TEST FIXTURE: She has welcomed contact.'],'uncertainties':['TEST FIXTURE: What support she wants.'],'clarification':'What has she asked for?',
      'areas':[{'key':k,'focus':'TEST FIXTURE: an aspect of support.','question':f'TEST FIXTURE: What does {NAMES[k]} invite you to consider?','followup':'Use only what she has said.','referenceIds':[r]} for k,r in zip(KEYS,['luke-22-42','psalm-139-23-24','matthew-26-37-39','romans-12-1-2','ephesians-2-8-10'])],
      'options':[{'action':'Offer to listen first.','reason':'She asked to be heard.','caution':'Ask before advising.','referenceIds':['proverbs-15-22']}],'safetyNote':''},'model':'gpt-5.4-mini (test fixture)','at':'2026-10-09T10:00:00Z'}
  forms={'sentence':'TEST FIXTURE: Father, help me listen with patience.','whems':{k:'TEST FIXTURE: Father, help me pray honestly in this area.' for k in KEYS},
         'extended':'TEST FIXTURE - not a historical prayer. '+('Father, teach me to listen with patience and wisdom. '*60)}
  t=data.get('target','all')
  if t!='all': forms={t:forms[t]}
  return {'result':forms,'model':'gpt-5.4-mini (test fixture)','at':'2026-10-09T10:00:00Z'}

class Session:
  """One browser context and page per check, so no state leaks between checks."""
  def __init__(self,w,h,forced=False):
    opts={'viewport':{'width':w,'height':h},'accept_downloads':True}
    if forced: opts['forced_colors']='active'
    self.ctx=browser.new_context(**opts);self.ctx.add_init_script(INIT_JS)
    self.api=[];self.dialogs=[];self.errors=[];self.console=[];self.requests=[];self.blocked=[];self.marked=0;self.headers={};self.pages=[]
    self.ctx.route('**/*',self._gate)
    self.ctx.route('https://www.esv.org/**',lambda r:r.fulfill(body='<p>Crossway transport fixture - not Bible text.</p>',content_type='text/html'))
    self.ctx.route('**/api/scripture*',lambda r:r.fulfill(status=200,json={'id':r.request.url.split('id=')[-1],'translation':'ESV','mode':'crossway-embed'}))
    self.ctx.route('**/api/guidance',self._guidance)
    self.ctx.on('page',self._wire)
    self.page=self.ctx.new_page();self.page.set_default_timeout(6000)
  def _gate(self,route):
    u=route.request.url
    if MODE=='http' and u.startswith(URL): route.continue_()
    else: self.blocked.append(u);route.abort()
  def _guidance(self,route):
    data=route.request.post_data_json;self.api.append(data);route.fulfill(status=200,json=guidance_fixture(data))
  def _wire(self,p):
    self.pages.append(p)
    p.on('dialog',lambda d:(self.dialogs.append(d.type+': '+d.message),d.accept()))
    p.on('pageerror',lambda e:self.errors.append(str(e)))
    p.on('console',lambda m:self.console.append(m.text) if re.search(r'Content.Security.Policy|Refused to',m.text) else None)
    p.on('request',lambda r:self.requests.append(r.url))
  def open(self,hash=''):
    p=self.page
    if MODE=='http':
      resp=p.goto(URL+('#'+hash if hash else ''),wait_until='networkidle');self.headers=dict(resp.headers) if resp else {}
    else: dom_load(p)
    p.wait_for_selector('#main h1',state='attached')
    p.wait_for_timeout(150);self.mark();return p
  def mark(self): self.marked=len(self.requests)
  def since(self): return [u for u in self.requests[self.marked:] if not u.endswith('/favicon.ico') and not u.startswith(('data:','blob:'))]
  def calls(self): return len(self.api) if MODE=='http' else self.page.evaluate('window.apiCalls.length')
  def writes(self): return self.page.evaluate('window.__sp.writes') if MODE=='http' else self.page.evaluate('window.testWrites')
  def close(self):
    try: self.ctx.close()
    except Exception: pass
  def __enter__(self): return self
  def __exit__(self,*a): self.close()

def dom_load(p):
  html=(PUBLIC/'index.html').read_text();html=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S);html=re.sub(r'<link\b[^>]*>','',html)
  p.set_content(html);p.add_style_tag(content=(PUBLIC/'styles.css').read_text());p.add_style_tag(content=(PUBLIC/'experience.css').read_text())
  p.evaluate("""()=>{const data={};window.testWrites=0;window.apiCalls=[];
    Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.hasOwn(data,k)?data[k]:null,setItem:(k,v)=>{window.testWrites++;data[k]=String(v);},removeItem:k=>{window.testWrites++;delete data[k];}}});
    window.open=()=>null;}""")
  for name in ['experience.js','build-info.js','theme.js','core.js','catalogue.js','teaching.js','prayer-output.js','guidance-core.js','journal.js','journey-ui.js','export.js','about.js','app.js']:
    p.add_script_tag(content=(PUBLIC/name).read_text())
  p.expose_function('spGuidance',guidance_fixture)
  p.evaluate("""()=>{window.fetch=async(url,opts)=>{
    if(String(url).includes('/api/scripture'))return {ok:true,json:async()=>({id:String(url).split('id=')[1],translation:'ESV',mode:'crossway-embed'})};
    const data=JSON.parse(opts.body);window.apiCalls.push(data);const r=await window.spGuidance(data);return {ok:true,json:async()=>r};};}""")

# ---------- small helpers ----------
def settle(p,ms=220): p.wait_for_timeout(ms)
def wait_js(p,expr,msg,arg=None,timeout=2500):
  try: p.wait_for_function(expr,arg=arg,timeout=timeout)
  except PWTimeout: raise AssertionError(msg)
def need(p,sel,what):
  n=p.locator(sel).count();assert n>0,f'{what} missing ({sel})';return p.locator(sel).first
def focus_in(p,sel,msg,timeout=2500): wait_js(p,"(s)=>{const e=document.querySelector(s);return !!e&&e.contains(document.activeElement);}",msg,sel,timeout)
def forms_filled(p,msg='the three prayers were not filled'): wait_js(p,"()=>{const f=[...document.querySelectorAll('[data-prayer-form]')];return f.length===3&&f.every(t=>t.value.trim().length>0);}",msg,timeout=4000)
def forms_values(p): return p.evaluate("()=>[...document.querySelectorAll('[data-prayer-form]')].map(t=>t.value)")
def overflow(p): return p.evaluate('()=>document.documentElement.scrollWidth-innerWidth')
def inner_h(p): return p.evaluate('()=>innerHeight')
def scroll_to(p,y): return p.evaluate(js('return go(arg);'),y)
def storage_state(p):
  """Every stored key and value, so a check can prove nothing changed (HTTP mode only)."""
  if MODE!='http': return None
  return p.evaluate("()=>JSON.stringify(Object.entries(localStorage).sort())+'|session:'+sessionStorage.length")
def storage_keys(p): return p.evaluate("()=>({local:Object.keys(localStorage).sort(),session:sessionStorage.length})") if MODE=='http' else None
def control(p,within,text,whole=False):
  """Buttons or links inside `within` whose words (aria-hidden parts removed) start with `text`, outside validation notes."""
  return p.evaluate(js(r'''const q=arg.t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const re=new RegExp('^'+q+(arg.whole?'(?![A-Za-z])':''));
    const root=document.querySelector(arg.w);if(!root)return [];
    return byText(root,'button,a,[role=button]',re).filter(e=>!e.closest('.field-action-note,.action-feedback,#reader')).map(e=>{if(!e.dataset.sp)e.dataset.sp=Math.random().toString(36).slice(2);return {id:e.dataset.sp,visible:vis(e),locate:e.getAttribute('data-locate'),text:W(e)};});'''),{'w':within,'t':text,'whole':whole})
def click_id(p,id): p.locator(f'[data-sp="{id}"]').click()  # data-sp marks a control found by its words
def fill_issue(p,text=ISSUE): p.locator('#guidance-issue').fill(text)
def quick_tap(s,issue=ISSUE):
  p=s.page
  if issue is not None: fill_issue(p,issue)
  need(p,'#quick-pray','the quick button "'+QUICK+'"');p.locator('#quick-pray').click()
def shot(p,name):
  try: p.screenshot(path=str(OUT/name))
  except Exception: pass
def set_reading(p,size):
  """Chooses a reading size through the header Text size control; returns a problem or None."""
  if p.locator('[data-action=text-size]').count()==0: return 'no Text size control'
  p.locator('[data-action=text-size]').first.click()
  try: p.locator('#reader').wait_for(state='visible',timeout=2500)
  except PWTimeout: return 'the Text size panel did not open'
  found=p.evaluate(js(r'''const b=[...document.querySelectorAll('#reader [data-action=size]')];const words=e=>T(e).replace(/\bChosen\b/g,'').replace(/[()]/g,'').trim();
    const m=b.find(e=>words(e)===arg);if(m){m.dataset.sp='size-'+arg;return {id:m.dataset.sp,all:b.map(words)};}return {id:null,all:b.map(words)};'''),size)
  if not found['id']:
    p.keyboard.press('Escape');settle(p,120);return f'no "{size}" reading-size button (found {found["all"]})'
  click_id(p,found['id']);settle(p,120)
  return None
def close_reader(p):
  if p.locator('#reader[open]').count():
    if p.locator('#reader [data-action=reader-close]').count(): p.locator('#reader [data-action=reader-close]').click()
    else: p.keyboard.press('Escape')
    settle(p,120)
def dismiss_notice(p):
  if p.locator('#notice .notice-dismiss').count() and p.locator('#notice').is_visible(): p.locator('#notice .notice-dismiss').click();settle(p,120)
def nav_to(p,route):
  dismiss_notice(p);close_reader(p);p.locator(f'.site-header nav [data-route={route}]').click();settle(p,300)
def save_entry(s):
  """Taps Save; in HTTP mode the download tab opens and is closed again. Returns the saved entry id."""
  p=s.page
  if MODE=='http':
    with s.ctx.expect_page(timeout=6000) as ev: p.locator('[data-action=save]').first.click()
    ev.value.close()
  else: p.locator('[data-action=save]').first.click()
  settle(p,300)
  ids=p.evaluate("()=>JSON.parse(localStorage.getItem('"+JOURNAL_KEY+"')||'{\"entries\":[]}').entries.map(e=>e.id)")
  return ids[0] if ids else None
def bar_visible(p): return p.evaluate(js("const t=document.getElementById('page-tools');return !!t&&vis(t);"))
def show_bar(p,screens=3):
  """Scrolls past two screens, where the floating bar is allowed to appear (A18)."""
  scroll_to(p,screens*inner_h(p));settle(p,160);return bar_visible(p)
KEYBOARD_ON="""(g)=>{window.__realVV=window.__realVV||window.visualViewport;Object.defineProperty(window,'visualViewport',{configurable:true,value:{width:g[0],height:g[1],offsetTop:0,offsetLeft:0,scale:1,addEventListener(){},removeEventListener(){}}});dispatchEvent(new Event('resize'));}"""
KEYBOARD_OFF="""()=>{Object.defineProperty(window,'visualViewport',{configurable:true,value:window.__realVV});dispatchEvent(new Event('resize'));}"""

QUICK_CONTRACT=js(r'''const p=[];const q=document.querySelectorAll('[data-quick-pray]'),b=document.getElementById('quick-pray');
if(!b)return ['#quick-pray missing'];
if(q.length!==1||q[0]!==b)p.push('exactly one [data-quick-pray], on #quick-pray, expected; found '+q.length);
if(b.tagName!=='BUTTON'||b.type!=='button')p.push('#quick-pray must be a <button type="button">');
if(b.hasAttribute('data-guide-action'))p.push('#quick-pray must not carry data-guide-action');
if(!b.classList.contains('primary'))p.push('#quick-pray must be primary-styled');
if(!W(b).includes(arg))p.push('#quick-pray reads "'+W(b)+'"');
const issue=document.getElementById('guidance-issue'),card=document.getElementById('guide-issue');
if(!card||!card.contains(b))p.push('#quick-pray is not inside #guide-issue');
if(issue&&!before(issue,b))p.push('#quick-pray does not follow #guidance-issue');
for(const s of ['[data-journey=context]','#guide-consent']){const e=document.querySelector(s);if(e&&!before(b,e))p.push('#quick-pray must come before '+s);}
const loc=document.querySelectorAll('[data-guide-action=local]');
if(loc.length!==1)p.push('expected one [data-guide-action=local]; found '+loc.length);else if(!W(loc[0]).includes(arg))p.push('[data-guide-action=local] reads "'+W(loc[0])+'", outside the "'+arg+'" label family');
if(issue){const between=[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].filter(e=>vis(e)&&!e.disabled&&before(issue,e)&&before(e,b));
 if(between.length)p.push('focusable controls sit between the issue box and #quick-pray: '+between.map(name).join('; '));}
if(innerWidth<innerHeight&&issue&&vis(b)){const i=R(issue),r=R(b);if(!(r.y>i.y&&r.y-i.bottom<=96))p.push('in portrait #quick-pray must sit directly under the issue box (within 96px); gap '+Math.round(r.y-i.bottom)+'px');}
return p;''')
QUICK_RESULT=js(r'''const a=document.activeElement,pr=document.getElementById('guide-prayers'),box=document.getElementById('prayer-flow-status');
const d=WholeheartedJournal.blank();d.journey.issue=arg;const f=WholeheartedGuidance.local(d);
const vals=Object.fromEntries([...document.querySelectorAll('[data-prayer-form]')].map(t=>[t.dataset.prayerForm,t.value]));
return {inPrayers:!!pr&&pr.contains(a),focusY:a?R(a).y:null,focus:name(a),status:box&&vis(box)?W(box):'',consent:!!document.getElementById('guidance-consent')?.checked,
 feedback:[...document.querySelectorAll('.action-feedback')].some(vis),differs:['sentence','whems','extended'].filter(k=>vals[k]!==f[k]),
 extendedWords:(vals.extended||'').trim().split(/\s+/).length,extendedHasIssue:(vals.extended||'').includes(arg),
 formFeedback:[...document.querySelectorAll('[data-form-feedback]')].map(W),h:innerHeight,dialogOpen:!!document.querySelector('dialog[open]')};''')

# ---------- checks ----------
FIRST_SCREEN=js(r'''const i=document.getElementById('guidance-issue'),q=document.getElementById('quick-pray'),intro=document.getElementById('prayer-introduction');
const fold=intro?[...intro.querySelectorAll('details')].find(d=>/^Show two short example prayers$/.test(W(d.querySelector('summary')))):null;
const coverOf=(e,x,y)=>{if(y<0||y>=innerHeight||x<0||x>=innerWidth)return 'off screen';const hit=document.elementFromPoint(x,y);if(!hit)return 'nothing';return e.contains(hit)||hit.contains(e)?null:name(hit.closest('#page-tools,#notice')||hit);};
let issue=null;
if(i){const cs=getComputedStyle(i),lh=cs.lineHeight==='normal'?parseFloat(cs.fontSize)*1.2:parseFloat(cs.lineHeight);const r=R(i);const lineTop=r.y+parseFloat(cs.borderTopWidth)+parseFloat(cs.paddingTop);
 issue={top:r.y+scrollY,y:r.y,firstLineBottom:lineTop+lh,cover:coverOf(i,r.x+r.w/2,lineTop+lh/2)};}
let quick=null;if(q&&vis(q)){const r=R(q);quick={y:r.y,bottom:r.bottom,centreOn:r.y+r.h/2>=0&&r.y+r.h/2<innerHeight,cover:coverOf(q,r.x+r.w/2,r.y+r.h/2)};}
return {issue,quick,h:innerHeight,scrollY,focusedIssue:!!i&&document.activeElement===i,h2:W(intro?.querySelector('h2')),
 fold:!!fold,foldOpen:!!fold?.open,foldHolds:!!fold&&/During conflict/.test(fold.textContent)&&/Afterwards - thanksgiving/.test(fold.textContent)};''')
def first_screen():
  probs=[]
  for w,h in PORTRAIT+LANDSCAPE:
    with Session(w,h) as s:
      p=s.open();shot(p,f'first-{w}x{h}.png')
      m=p.evaluate(FIRST_SCREEN);tag=f'{w}x{h}'
      if m['scrollY']>0: probs.append(f"{tag}: the page is scrolled to {m['scrollY']:.0f}px on load; the first screen must be measured unscrolled")
      if m['focusedIssue']: probs.append(tag+': the issue box is focused on load, which raises the phone keyboard')
      if m['issue'] is None: probs.append(tag+': #guidance-issue missing');continue
      i,q=m['issue'],m['quick']
      if w<h:
        limit=1.1*m['h'] if (w,h)==(320,568) else m['h']
        if i['top']>=limit: probs.append(f"{tag}: issue box starts at {i['top']:.0f}px in the document; limit {limit:.0f}px ({i['top']/m['h']:.2f} screens)")
        if q and q['centreOn'] and q['cover']: probs.append(f"{tag}: #quick-pray is covered by {q['cover']}")
      else:
        if i['y']<0 or i['firstLineBottom']>m['h']: probs.append(f"{tag}: the issue box's first text line is not on the first screen (y {i['y']:.0f}, first line ends {i['firstLineBottom']:.0f}, screen {m['h']})")
        elif i['cover']: probs.append(f"{tag}: the issue box is covered by {i['cover']}")
        if not q: probs.append(tag+': #quick-pray missing or hidden')
        elif q['y']<0 or q['bottom']>m['h']: probs.append(f"{tag}: #quick-pray is not fully on the first screen (y {q['y']:.0f}-{q['bottom']:.0f}, screen {m['h']})")
        elif q['cover']: probs.append(f"{tag}: #quick-pray is covered by {q['cover']}")
      if m['h2']!='A simple W.H.E.M.S. prayer pattern': probs.append(tag+': #prayer-introduction h2 changed or missing')
      if not m['fold']: probs.append(tag+': no closed "Show two short example prayers" details in #prayer-introduction')
      elif m['foldOpen'] or not m['foldHolds']: probs.append(tag+': the example-prayer fold is open or does not hold both example prayers')
  assert not probs,' | '.join(probs[:14])+(f' | ...{len(probs)-14} more' if len(probs)>14 else '')

def quick_issue_only():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';contract=p.evaluate(QUICK_CONTRACT,QUICK)
      if '#quick-pray missing' in contract: probs.append(tag+': #quick-pray ("'+QUICK+'") missing under the issue box');continue
      probs+=[tag+': '+x for x in contract]
      stored=storage_state(p);fill_issue(p);s.mark();p.locator('#quick-pray').click()
      try: forms_filled(p)
      except AssertionError as e: probs.append(tag+': '+str(e));continue
      settle(p,400);shot(p,f'quick-{tag}.png')
      st=p.evaluate(QUICK_RESULT,ISSUE)
      if s.calls(): probs.append(f'{tag}: {s.calls()} /api/guidance request(s)')
      if s.writes(): probs.append(f'{tag}: {s.writes()} storage write(s)')
      if stored is not None and storage_state(p)!=stored: probs.append(tag+': browser storage changed')
      if s.dialogs: probs.append(tag+': dialog: '+s.dialogs[0])
      if st['dialogOpen']: probs.append(tag+': a <dialog> is open after the quick tap')
      if s.since(): probs.append(tag+': network request(s): '+', '.join(s.since()[:3]))
      if not st['inPrayers']: probs.append(tag+': focus is not in #guide-prayers ('+st['focus']+')')
      elif not (0<=st['focusY']<st['h']): probs.append(tag+': the focused prayers element is off screen')
      if 'Nothing was sent' not in st['status']: probs.append(tag+': #prayer-flow-status does not say "Nothing was sent"')
      if not st['consent']: probs.append(tag+': the consent box lost its default tick (A28)')
      if st['feedback']: probs.append(tag+': validation feedback appeared')
      if st['differs']: probs.append(tag+': the quick path must fill exactly WholeheartedGuidance.local(draft) (A3); '+', '.join(st['differs'])+' differ')
      if not (450<=st['extendedWords']<=900): probs.append(f"{tag}: extended prayer has {st['extendedWords']} words; 450 to 900 expected (I17)")
      if not st['extendedHasIssue']: probs.append(tag+': the extended prayer does not contain the issue (I17)')
      if len(st['formFeedback'])!=3 or not all('Local starting prayer' in t for t in st['formFeedback']): probs.append(tag+': every [data-form-feedback] must say "Local starting prayer"')
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

def quick_blank_issue():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      if not p.locator('#quick-pray').count(): probs.append(tag+': the quick button is missing (#quick-pray)');continue
      stored=storage_state(p);s.mark();p.locator('#quick-pray').click()
      try:
        wait_js(p,"()=>[...document.querySelectorAll('.action-feedback')].some(e=>e.getClientRects().length)",'no visible .action-feedback after an empty quick tap')
        focus_in(p,'#guidance-issue','focus did not move to #guidance-issue')
      except AssertionError as e: probs.append(tag+': '+str(e));continue
      if p.locator('#guidance-issue').get_attribute('aria-invalid')!='true': probs.append(tag+': #guidance-issue lacks aria-invalid="true"')
      n=p.locator('.action-feedback li').count()
      if n>1: probs.append(f'{tag}: {n} prerequisites listed; only the issue is needed for the quick path')
      if s.calls() or s.since(): probs.append(tag+': something was sent')
      if s.writes() or (stored is not None and storage_state(p)!=stored): probs.append(tag+': storage was written')
      if s.dialogs: probs.append(tag+': dialog: '+s.dialogs[0])
      if any(v.strip() for v in forms_values(p)): probs.append(tag+': prayers were filled without an issue')
      if not p.locator('#guidance-consent').is_checked(): probs.append(tag+': the consent box lost its default tick (A28)')
  assert not probs,' | '.join(probs)

TAP_PREP="""()=>{const d=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value');window.__formSets=0;
  Object.defineProperty(HTMLTextAreaElement.prototype,'value',{configurable:true,get(){return d.get.call(this);},set(v){if(this.matches('[data-prayer-form]'))window.__formSets++;d.set.call(this,v);}});
  window.__taps=[];document.addEventListener('click',e=>{if(e.target.closest&&e.target.closest('#quick-pray'))window.__taps.push(performance.now());},true);}"""
def double_tap(w,h,gap_ms,same_point):
  tag=f"{w}x{h} {'same point' if same_point else 'element-targeted'} second tap after {gap_ms}ms"
  with Session(w,h) as s:
    p=s.open()
    if not p.locator('#quick-pray').count(): return [tag+': the quick button is missing (#quick-pray)']
    fill_issue(p);p.evaluate(TAP_PREP)
    b=p.locator('#quick-pray');b.scroll_into_view_if_needed();settle(p,150);r=b.bounding_box()
    x,y=r['x']+r['width']/2,r['y']+r['height']/2
    t0=time.monotonic();p.mouse.click(x,y)
    try: forms_filled(p,'the first tap did not fill the prayers')
    except AssertionError as e: return [tag+': '+str(e)]
    sets1=p.evaluate('window.__formSets');vals1=forms_values(p)
    p.wait_for_timeout(max(0,int(gap_ms-(time.monotonic()-t0)*1000)))
    if same_point: p.mouse.click(x,y)
    else: p.evaluate("()=>document.getElementById('quick-pray').click()")
    settle(p,1000)
    st=p.evaluate("()=>({taps:window.__taps,sets:window.__formSets,open:!!document.querySelector('dialog[open]')})");probs=[]
    if not same_point:
      if len(st['taps'])!=2: probs.append(f"{tag}: {len(st['taps'])} click(s) reached #quick-pray; expected 2")
      elif not (st['taps'][1]-st['taps'][0]<800): probs.append(f"{tag}: the taps were {st['taps'][1]-st['taps'][0]:.0f}ms apart in the page; the fixture needs under 800ms")
    if s.dialogs: probs.append(tag+': a dialog appeared: '+s.dialogs[0])
    if st['open']: probs.append(tag+': a <dialog> opened')
    if st['sets']!=sets1: probs.append(f"{tag}: the second tap wrote the prayer boxes again ({st['sets']-sets1} more write(s))")
    if forms_values(p)!=vals1: probs.append(tag+': the second tap changed the prayers')
    if not all(v.strip() for v in forms_values(p)): probs.append(tag+': the prayers are not filled')
    if s.calls() or s.writes(): probs.append(tag+': something was sent or stored')
    return probs
def quick_double_tap():
  probs=double_tap(390,844,150,False)+double_tap(390,844,700,False)+double_tap(390,844,150,True)+double_tap(844,390,300,True)
  assert not probs,' | '.join(probs)

def go_to_save():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      if not p.locator('#quick-pray').count(): probs.append(tag+': the quick button "'+QUICK+'" is missing (#quick-pray)');continue
      quick_tap(s)
      try: forms_filled(p)
      except AssertionError as e: probs.append(tag+': '+str(e));continue
      settle(p,300)
      found=control(p,'#prayer-flow-status','Go to Save')
      if not found: probs.append(tag+': no "Go to Save" control in #prayer-flow-status');continue
      if found[0]['locate']!='#guide-save': probs.append(tag+': "Go to Save" must carry data-locate="#guide-save"')
      click_id(p,found[0]['id'])
      try: focus_in(p,'#guide-save','"Go to Save" did not focus #guide-save')
      except AssertionError as e: probs.append(tag+': '+str(e));continue
      settle(p,300)
      r=p.evaluate(js(r'''const b=document.querySelector('#guide-save [data-action=save]');if(!b)return null;const r=R(b);const e=r.y>=0&&r.bottom<=innerHeight?document.elementFromPoint(r.x+r.w/2,r.y+r.h/2):null;return {...r,v:vis(b),h:innerHeight,hit:!!e&&b.contains(e),hitName:e?name(e.closest('#page-tools,#notice')||e):'off screen'};'''))
      if not r: probs.append(tag+': no Save button in #guide-save');continue
      if not (r['v'] and r['y']>=0 and r['bottom']<=r['h']): probs.append(f"{tag}: Save is not fully on screen after Go to Save (y {r['y']:.0f}-{r['bottom']:.0f}, screen {r['h']})")
      elif not r['hit']: probs.append(f"{tag}: the Save button is covered by {r['hitName']}")
      if s.writes(): probs.append(tag+': stored before Save was tapped');continue
      shot(p,f'go-to-save-{tag}.png')
      save_entry(s)
      if MODE!='http' and 'Saved on this device' not in p.locator('#notice').inner_text(): probs.append(tag+': Save did not report success')
      entries=p.evaluate("()=>JSON.parse(localStorage.getItem('"+JOURNAL_KEY+"')||'{\"entries\":[]}').entries")
      if not (len(entries)==1 and entries[0]['journey']['issue']==ISSUE and all(entries[0]['prayerForms'][k].strip() for k in ['sentence','whems','extended'])): probs.append(tag+': one tap on Save did not keep the issue and all three prayers')
      if s.writes()!=1: probs.append(f'{tag}: {s.writes()} storage writes; expected exactly one, by Save')
      keys=storage_keys(p)
      if keys and (keys['local']!=[JOURNAL_KEY] or keys['session']): probs.append(f"{tag}: storage holds {keys['local']} and {keys['session']} session item(s); only {JOURNAL_KEY} is allowed (I7)")
      if s.calls() or s.dialogs: probs.append(tag+': something was sent or a dialog appeared')
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

AI_STATE=js(r'''const e=document.getElementById('ai-state');return e?{text:W(e),visible:vis(e),inPrayers:!!e.closest('#guide-prayers'),live:['polite','assertive'].includes(e.getAttribute('aria-live'))||['status','alert','log'].includes(e.getAttribute('role'))}:null;''')
def ai_quick_path():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';fill_issue(p)
      first=p.evaluate(AI_STATE)
      if not first: probs.append(tag+': #ai-state line missing')
      else:
        if not (first['visible'] and first['inPrayers']): probs.append(tag+': #ai-state must be visible inside #guide-prayers')
        if not first['live']: probs.append(tag+': #ai-state must be a live region (aria-live polite/assertive or role status)')
      go=control(p,'#guide-prayers','Go to the AI permission box')
      if not go: probs.append(tag+': no "Go to the AI permission box" control in #guide-prayers')
      else:
        if go[0]['locate']!='#guidance-consent': probs.append(tag+': "Go to the AI permission box" must carry data-locate="#guidance-consent"')
        click_id(p,go[0]['id'])
        try: focus_in(p,'#guidance-consent','x')
        except AssertionError: probs.append(tag+': "Go to the AI permission box" did not focus #guidance-consent')
        settle(p,200)
        if not p.locator('#guidance-consent').is_checked(): probs.append(tag+': navigation unticked consent (A28: ticked by default)')
      p.locator('#guidance-consent').uncheck();settle(p,150)   # A28: the box starts ticked, so the wording check runs the other way round
      after=p.evaluate(AI_STATE)
      if first and after:
        if after['text']==first['text'] or first['text'].find(after['text'])>=0: probs.append(f"{tag}: #ai-state does not change when consent is unticked (\"{first['text']}\" -> \"{after['text']}\")")
        p.locator('#guidance-consent').check();settle(p,150)
        again=p.evaluate(AI_STATE)
        if again['text']!=first['text']: probs.append(f"{tag}: #ai-state does not return to its original wording when consent is ticked again (\"{again['text']}\")")
      p.locator('#guidance-consent').check();settle(p,150)
      mine=control(p,'#guide-consent','Go to my prayers')
      if mine: click_id(p,mine[0]['id']);settle(p,300)
      p.locator('#guide-prayers-ai').click()
      try: forms_filled(p,'the AI prayers did not fill')
      except AssertionError as e: probs.append(tag+': '+str(e))
      settle(p,300)
      if s.calls()!=1: probs.append(f'{tag}: {s.calls()} AI requests; expected exactly one')
      else:
        sent=s.api[0] if MODE=='http' else p.evaluate('window.apiCalls[0]')
        if sent.get('action')!='prayers' or sent.get('consent') is not True or sent.get('summary'): probs.append(tag+': the one request is not a consented prayers request without a summary')
      if p.evaluate("()=>[...document.querySelectorAll('.action-feedback')].some(e=>e.getClientRects().length)"): probs.append(tag+': a summary or consent gate appeared without a reflection')
      if p.locator('#guidance-confirm').count(): probs.append(tag+': the understanding acknowledgement appeared without a reflection')
      if s.writes() or s.dialogs: probs.append(tag+': stored or raised a dialog')
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

def deep_path_navigation():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      deeper=control(p,'#guide-issue',DEEPER)
      if not deeper: probs.append(tag+': no "'+DEEPER+'" control in #guide-issue');continue
      click_id(p,deeper[0]['id']);settle(p,400)
      f=p.evaluate(js(r'''const a=document.activeElement,w=document.getElementById('reflection-W'),card=document.getElementById('guide-issue');
        return {name:name(a),y:a?R(a).y:-1,h:innerHeight,ok:!!a&&a!==document.body&&!!w&&!card.contains(a)&&before(card,a)&&(w.contains(a)||before(a,w))};'''))
      if not f['ok']: probs.append(tag+': "'+DEEPER+'" did not move focus to the start of the five areas ('+f['name']+')')
      elif not (0<=f['y']<f['h']): probs.append(tag+': the deep-path start is off screen after "'+DEEPER+'"')
      for k,n in NEXT.items():
        c=control(p,'#reflection-'+k,'Next: '+NAMES[n],whole=True)
        if not c: probs.append(f'{tag}: no "Next: {NAMES[n]}" button in #reflection-{k}');continue
        if not c[0]['visible']: probs.append(f'{tag}: "Next: {NAMES[n]}" is hidden');continue
        click_id(p,c[0]['id'])
        try: focus_in(p,'#reflection-'+n,'x')
        except AssertionError: probs.append(f'{tag}: "Next: {NAMES[n]}" did not focus #reflection-{n}');continue
        settle(p,250)
        y=p.evaluate("()=>[document.activeElement.getBoundingClientRect().top,innerHeight]")
        if not (0<=y[0]<y[1]): probs.append(f'{tag}: #reflection-{n} focus target is off screen ({y[0]:.0f}px)')
      soul=control(p,'#reflection-S','Next:')
      if soul and soul[0]['visible']:
        click_id(p,soul[0]['id']);settle(p,400)
        if p.evaluate(js(r'''const s=document.getElementById('reflection-S'),a=document.activeElement;return s.contains(a)||!before(s,a);''')): probs.append(tag+': the Soul "Next:" button does not move past Soul')
      shot(p,f'deep-path-{tag}.png')
      hidden=p.evaluate(js("return ['W','H','E','M','S'].filter(k=>!vis(document.querySelector('[data-guide-reply='+k+']')));"))
      if hidden: probs.append(tag+': reply boxes not visible: '+', '.join(hidden))
      if p.locator('.open-area').count()!=5: probs.append(tag+': the five open areas changed')
      if s.calls() or s.writes() or s.dialogs: probs.append(tag+': navigation sent, stored or raised a dialog')
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

ACCENT_NAMES=r'''const accentNames=new Set(['--action']);for(const sh of document.styleSheets){let rules;try{rules=sh.cssRules;}catch(e){continue;}const walk=rs=>{for(const r of rs){if(r.style)for(let i=0;i<r.style.length;i++){const n=r.style[i];if(/^--.*(gilt|gold)/i.test(n))accentNames.add(n);}if(r.cssRules)walk(r.cssRules);}};walk(rules);}
const accentValues=new Set([...accentNames].map(n=>probe('var('+n+')')));accentValues.delete('rgba(0, 0, 0, 0)');'''
PRIMARY_SCAN=js(ACCENT_NAMES+r'''const paper=probe('var(--paper)');
const rgb=s=>{const m=String(s).match(/rgba?\(([^)]+)\)/);if(!m)return null;const v=m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);return {r:v[0],g:v[1],b:v[2],a:v.length>3?v[3]:1};};
const lum=c=>[c.r,c.g,c.b].map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
const contrast=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
const P=rgb(paper);
const isPrimary=e=>{if(e.classList.contains('primary'))return true;const c=rgb(getComputedStyle(e).backgroundColor);return !!c&&!!P&&c.a>=0.5&&contrast(c,P)>=4.5;};
const usesAccent=e=>{const cs=getComputedStyle(e);if(accentValues.has(cs.color)||accentValues.has(cs.backgroundColor))return true;if(cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>0&&accentValues.has(cs.outlineColor))return true;for(const s of ['Top','Right','Bottom','Left'])if(cs['border'+s+'Style']!=='none'&&parseFloat(cs['border'+s+'Width'])>0&&accentValues.has(cs['border'+s+'Color']))return true;return false;};
const controls=[...document.querySelectorAll('button,a[href],summary,[role=button],input[type=submit],input[type=button]')];
const everything=[...document.querySelectorAll('.site-header *, #main *, #page-tools *')];
const onScreen=e=>{const r=e.getBoundingClientRect();return Math.min(r.bottom,innerHeight)-Math.max(r.top,0)>=8;};
const out=[];const step=Math.round(innerHeight/2),max=document.documentElement.scrollHeight;
for(let y=0;;y+=step){go(y);const seen=controls.filter(e=>vis(e)&&isPrimary(e)&&onScreen(e)).map(name);const accents=everything.filter(e=>vis(e)&&onScreen(e)&&usesAccent(e)).length;out.push({y:scrollY,seen,accents});if(scrollY+innerHeight>=max-1)break;}
go(0);return out;''')
def one_primary_per_screen():
  probs=[];maxAccents=0
  for w,h in [(390,844),(375,667)]:
    with Session(w,h) as s:
      p=s.open()
      for state in ['fresh','after quick prayers']:
        if state!='fresh':
          if not p.locator('#quick-pray').count(): break
          quick_tap(s);forms_filled(p);settle(p,300)
        p.mouse.move(0,0);scans=p.evaluate(PRIMARY_SCAN)
        for sc in scans:
          maxAccents=max(maxAccents,sc['accents'])
          if len(sc['seen'])>1: probs.append(f"{w}x{h} {state} at y={sc['y']:.0f}: {len(sc['seen'])} primary-styled controls: {'; '.join(sc['seen'][:3])}")
  assert not probs,' | '.join(probs[:8])+(f' | ...{len(probs)-8} more' if len(probs)>8 else '')
  return f'NOTE at most one primary-styled control per screen-height; "exactly one" is an open reading for the owner; accent uses per half-screen sample: max {maxAccents} (A8 asks for at most 3; advisory, owner screenshot review)'

def save_promise_line():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open()
      m=p.evaluate(js(r'''const all=[...document.querySelectorAll('#main *')].filter(e=>W(e).includes(arg)&&![...e.children].some(c=>W(c).includes(arg)));
        const i=document.getElementById('guidance-issue');
        return all.map(e=>({in:!!e.closest('#guide-issue'),visible:vis(e),details:!!e.closest('details:not([open])'),gap:i?gap(R(e),R(i)):null,exact:W(e)===arg}));'''),SAVE_PROMISE)
      tag=f'{w}x{h}'
      if not m: probs.append(tag+': "'+SAVE_PROMISE+'" is not on the page');continue
      good=[x for x in m if x['in'] and x['visible'] and not x['details']]
      if not good: probs.append(tag+': the save promise is not visible inside #guide-issue')
      elif w<h and min(x['gap'] for x in good)>h*0.5: probs.append(tag+': the save promise is not near the issue box')
  assert not probs,' | '.join(probs)

def uncovered_topics(items):
  """Maximum matching of the ten topic families to distinct list items (an item naming two topics with "or"/"and" may take two)."""
  slots=[]
  for ii,t in enumerate(items): slots+=[ii]*(2 if re.search(r'\b(or|and)\b',t,re.I) else 1)
  fams=list(SAFETY_TOPICS.items());owner={}
  def dfs(fi,seen):
    for si,ii in enumerate(slots):
      if si in seen or not re.search(fams[fi][1],items[ii],re.I): continue
      seen.add(si)
      if si not in owner or dfs(owner[si],seen): owner[si]=fi;return True
    return False
  matched={fi for fi in range(len(fams)) if dfs(fi,set())}
  return [fams[fi][0] for fi in range(len(fams)) if fi not in matched]
def safety_list():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();s.mark();tag=f'{w}x{h}'
      m=p.evaluate(js(r'''const hs=[...document.querySelectorAll('#main h2,#main h3,#main h4,#main summary,#main strong,#main p')].filter(e=>W(e).startsWith(arg));
        if(!hs.length)return null;const h=hs[0];const d=h.closest('details');if(d&&!d.open){h.closest('summary')?.click();}
        let c=h;while(c&&c!==document.body&&!c.querySelector('ul,ol'))c=c.parentElement;const list=c&&c!==document.body?c.querySelector('ul,ol'):null;
        const i=document.getElementById('guidance-issue'),w=document.getElementById('reflection-W');
        return {items:list?[...list.querySelectorAll('li')].map(W):[],gap:i?gap(R(h),R(i)):null,beforeAreas:w?before(h,w):false,inAI:!!h.closest('#guide-consent,#guide-prayers,#guide-understanding-slot'),
          media:list?list.querySelectorAll('iframe,img,script,object,embed,svg,video,audio').length:0,visible:vis(h),h:innerHeight};'''),SAFETY)
      if not m: probs.append(tag+': no "'+SAFETY+'" list on the Pray screen');continue
      settle(p,200)
      missing=uncovered_topics(m['items'])
      if len(m['items'])<8: probs.append(f"{tag}: {len(m['items'])} list items; section 23 lists 10 topics")
      if missing: probs.append(tag+': topics without their own list item: '+', '.join(missing))
      if not m['visible']: probs.append(tag+': the list heading is not visible')
      if not m['beforeAreas'] or m['gap'] is None or m['gap']>m['h']: probs.append(tag+': the list is not near the issue box (before the areas, within one screen)')
      if m['inAI']: probs.append(tag+': the list sits inside an AI or prayer container')
      if m['media']: probs.append(tag+': the list carries media')
      if s.since() or s.calls(): probs.append(tag+': showing the list made a network request: '+', '.join(s.since()[:3]))
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

OVERFLOW_SCAN=js(r'''const out=[];const nav=[...document.querySelectorAll('.site-header a, .site-header button')].filter(vis);
if(document.documentElement.scrollWidth>innerWidth+1)out.push('page overflows by '+(document.documentElement.scrollWidth-innerWidth)+'px');
for(const e of nav){const r=R(e);if(r.x<-1||r.right>innerWidth+1){out.push('header control '+name(e)+' spills out');break;}}
const tools=document.getElementById('page-tools');
if(tools&&vis(tools)){const r=R(tools);if(r.x<-1||r.right>innerWidth+1||r.bottom>innerHeight+1||r.y<-1)out.push('#page-tools spills out ('+Math.round(r.x)+'-'+Math.round(r.right)+', y '+Math.round(r.y)+'-'+Math.round(r.bottom)+')');}
return out;''')
def measure_overflow(p,probs,tag):
  for x in p.evaluate(OVERFLOW_SCAN): probs.append(f'{tag}: {x}')
  scroll_to(p,3*inner_h(p));settle(p,120)
  for x in p.evaluate(OVERFLOW_SCAN): probs.append(f'{tag} (scrolled, bar shown): {x}')
  scroll_to(p,0)
def matrix_no_overflow():
  probs=[]
  with Session(390,844) as s:
    p=s.open()
    for size in SIZES:
      problem=set_reading(p,size);close_reader(p)
      if problem: probs.append(size+': '+problem);continue
      for w,h in PORTRAIT+LANDSCAPE+TABLETS:
        p.set_viewport_size({'width':w,'height':h});settle(p,90);measure_overflow(p,probs,f'Pray {size} {w}x{h}')
      p.set_viewport_size({'width':390,'height':844});settle(p,120);scroll_to(p,0);shot(p,f'matrix-{size.lower()}-390x844.png')
    if not set_reading(p,'Standard'):
      close_reader(p);p.set_viewport_size({'width':390,'height':844});p.evaluate("document.documentElement.style.fontSize='200%'");settle(p,150);measure_overflow(p,probs,'Pray 200% root 390x844')
      scroll_to(p,0);shot(p,'matrix-200pct-390x844.png');p.evaluate("document.documentElement.style.fontSize=''")
    for route,label in [('journal','Journal'),('browse','Browse'),('scripture','Scripture')]:
      if route=='browse': nav_to(p,'journal');p.locator('[data-action=browse]').first.click();settle(p,300)
      else: nav_to(p,route)
      for size in ['Larger','Largest']:
        problem=set_reading(p,size);close_reader(p)
        if problem: continue
        for w,h in PORTRAIT+LANDSCAPE:
          p.set_viewport_size({'width':w,'height':h});settle(p,80);measure_overflow(p,probs,f'{label} {size} {w}x{h}')
      p.set_viewport_size({'width':390,'height':844});set_reading(p,'Standard');close_reader(p)
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

TAP_SCAN=js(r'''const out=[];const inline=e=>{if(e.tagName!=='A')return false;const blk=e.parentElement;return getComputedStyle(e).display==='inline'&&blk&&T(blk).length>T(e).length+10;};
const floor=e=>e.matches('.site-header .brand')?32:e.matches('.site-header nav a, .site-header [data-action=text-size]')?40:48;
const items=new Set();const scope=document.querySelector(arg||'body')||document.body;for(const e of scope.querySelectorAll('button,summary,label.check,a[href],select,[role=button],input[type=checkbox],input[type=radio]')){if(e.matches('input'))items.add(e.closest('label')||e);else items.add(e);}
for(const e of items){if(!vis(e)||inline(e)||e.closest('.skip'))continue;const r=R(e),f=floor(e);if(r.h<f-0.5||(f!==32&&r.w<f-0.5))out.push(name(e)+' '+Math.round(r.w)+'x'+Math.round(r.h)+' (floor '+f+'px)');}
const q=document.getElementById('quick-pray');return {small:out,quick:q&&vis(q)?R(q).h:null};''')
def tour(s,visit):
  """Visits the screens a person reaches after the quick path and Save; visit(label, scope) records what it finds."""
  p=s.page;h=inner_h(p)
  visit('Pray fresh','body')
  if not p.locator('#quick-pray').count(): return
  quick_tap(s);forms_filled(p);settle(p,300);visit('Pray after quick prayers','body')
  if show_bar(p): visit('floating bar','#page-tools')
  scroll_to(p,0)
  if p.locator('[data-action=text-size]').count():
    p.locator('[data-action=text-size]').first.click();settle(p,200);visit('Text size panel','#reader');close_reader(p)
  id=save_entry(s);visit('Pray after Save, with the notice','body');dismiss_notice(p)
  nav_to(p,'journal');visit('Journal','body')
  p.locator('[data-action=browse]').first.click();settle(p,300);visit('Browse with one saved entry','body')
  p.locator('[data-action=open-entry]').first.click();settle(p,300);visit('Saved entry','body')
  if id: p.evaluate("(id)=>{location.hash='download-'+id;}",id);settle(p,300);visit('Download page','body')
  nav_to(p,'pray')
  for action,label in [('learn','Learn'),('about','About'),('privacy','Privacy')]:
    dismiss_notice(p);p.locator(f'[data-action={action}]').first.click();p.locator('#reader').wait_for();settle(p,250);visit(label,'#reader');close_reader(p)
  if show_bar(p) and p.locator('[data-fab=contents]').count():
    p.locator('[data-fab=contents]').first.click();p.locator('#reader').wait_for();settle(p,200);visit('Contents','#reader');close_reader(p)
  scroll_to(p,0)
  if p.locator('#reflection-W [data-verse]').count():
    p.locator('#reflection-W [data-verse]').first.click();p.locator('#reader').wait_for();settle(p,300);visit('Scripture reader','#reader');close_reader(p)
  nav_to(p,'scripture');visit('Scripture','body')
def tap_targets():
  probs=[]
  for w,h in [(320,568),(390,844),(844,390)]:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      def visit(label,scope):
        m=p.evaluate(TAP_SCAN,scope)
        probs.extend(f'{tag} {label}: {x}' for x in m['small'])
        if label=='Pray fresh':
          if m['quick'] is None: probs.append(tag+': #quick-pray missing')
          elif m['quick']<55.5: probs.append(f"{tag}: #quick-pray is {m['quick']:.0f}px tall; the main action needs 56px")
      tour(s,visit)
  probs=list(dict.fromkeys(probs))
  assert not probs,f'{len(probs)} controls under their floor: '+' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

TEXT_SCAN=js(r'''const out=[];let min=99;const scope=document.querySelector(arg)||document.body;const w=document.createTreeWalker(scope,NodeFilter.SHOW_TEXT);
while(w.nextNode()){const n=w.currentNode;if(!n.textContent.trim())continue;const el=n.parentElement;if(!el||el.closest('script,style,noscript,template')||!vis(el))continue;
 const range=document.createRange();range.selectNodeContents(n);const rs=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);if(!rs.length&&el.tagName!=='TEXTAREA')continue;
 if(el.closest('.skip'))continue;
 const fs=parseFloat(getComputedStyle(el).fontSize);if(fs<min)min=fs;if(fs<17.95)out.push(name(el)+' '+fs+'px');}
for(const e of scope.querySelectorAll('input:not([type=checkbox]):not([type=radio]),select,textarea,button')){if(!vis(e))continue;const fs=parseFloat(getComputedStyle(e).fontSize);if(fs<17.95)out.push('control '+name(e)+' '+fs+'px');}
return {min,small:[...new Set(out)],body:parseFloat(getComputedStyle(document.body).fontSize)};''')
CONTROL_SCAN=js(r'''return [...document.querySelectorAll('input:not([type=checkbox]):not([type=radio]),select,textarea,button')].filter(vis).map(e=>[name(e),parseFloat(getComputedStyle(e).fontSize)]).filter(x=>x[1]<17.95).map(x=>x[0]+' '+x[1]+'px');''')
SIZE_STATE=js(r'''return [...document.querySelectorAll('#reader [data-action=size]')].map(e=>({words:T(e).replace(/\bChosen\b/g,'').replace(/[()]/g,'').trim(),pressed:e.getAttribute('aria-pressed'),chosen:/\bChosen\b/.test(T(e))&&vis(e)}));''')
def body_px(p): return p.evaluate("()=>parseFloat(getComputedStyle(document.body).fontSize)")
def min_font():
  probs=[]
  for w,h in [(320,568),(390,844)]:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      def visit(label,scope):
        m=p.evaluate(TEXT_SCAN,scope)
        if m['small']: probs.append(f"{tag} {label}: {len(m['small'])} text runs under 18px, e.g. {'; '.join(m['small'][:4])}")
        if label=='Pray fresh' and abs(m['body']-20)>0.25: probs.append(f"{tag}: body text is {m['body']}px at Standard; expected 20px")
      tour(s,visit)
  with Session(390,844) as s:
    p=s.open();keys=storage_keys(p);bodies={}
    for size in SIZES:
      problem=set_reading(p,size)
      if problem: probs.append(size+': '+problem);close_reader(p);continue
      state=p.evaluate(SIZE_STATE);close_reader(p);bodies[size]=body_px(p)
      mine=[x for x in state if x['words']==size]
      if not mine or mine[0]['pressed']!='true': probs.append(f'{size}: the chosen size lacks aria-pressed="true"')
      if any(x['pressed']!='false' for x in state if x['words']!=size): probs.append(f'{size}: other sizes must carry aria-pressed="false"')
      if not mine or not mine[0]['chosen']: probs.append(f'{size}: the chosen size does not show the word "Chosen"')
      if any(x['chosen'] for x in state if x['words']!=size): probs.append(f'{size}: "Chosen" shows on a size that is not chosen')
      small=p.evaluate(CONTROL_SCAN)
      if small: probs.append(f"{size}: form controls under 18px: {'; '.join(small[:3])}")
    if 'Standard' in bodies:
      for size,ratio in [('Larger',1.25),('Largest',1.5)]:
        if size in bodies and abs(bodies[size]-bodies['Standard']*ratio)>0.6: probs.append(f"{size} body text is {bodies[size]}px; expected {ratio:.0%} of Standard ({bodies['Standard']*ratio:.1f}px)")
    if keys is not None and storage_keys(p)!=keys: probs.append('choosing a text size changed browser storage (I7)')
    if s.writes(): probs.append('choosing a text size wrote storage (I7)')
  assert not probs,' | '.join(probs[:10])+(f' | ...{len(probs)-10} more' if len(probs)>10 else '')

def rotation():
  probs=[]
  with Session(390,844) as s:
    p=s.open();s.mark()
    first,second='Should I speak to my son',' before he moves away?'
    p.locator('#guidance-issue').click();p.keyboard.type(first)
    p.set_viewport_size({'width':844,'height':390});settle(p,350);p.keyboard.type(second);settle(p,150)
    st=p.evaluate("()=>{const t=document.getElementById('guidance-issue');return {v:t.value,f:document.activeElement===t,c:t.selectionStart}}")
    if st['v']!=first+second: probs.append('typing across the rotation lost text: "'+st['v']+'"')
    if not st['f']: probs.append('focus left the issue box on rotation')
    if st['c']!=len(first+second): probs.append('the caret moved on rotation')
    if overflow(p)>1: probs.append(f'landscape overflow {overflow(p)}px')
    p.set_viewport_size({'width':390,'height':844});settle(p,350)
    if not p.evaluate("()=>document.activeElement===document.getElementById('guidance-issue')"): probs.append('focus left the issue box on rotating back')
    if p.locator('#guidance-issue').input_value()!=first+second: probs.append('rotating back lost text')
    if overflow(p)>1: probs.append(f'portrait overflow {overflow(p)}px')
    if s.calls() or s.since(): probs.append('rotation or typing sent a request')
    if s.writes(): probs.append('rotation or typing wrote storage')
    if s.dialogs: probs.append('dialog: '+s.dialogs[0])
    p.evaluate('document.activeElement.blur()')
    for w,h in LANDSCAPE:
      p.set_viewport_size({'width':w,'height':h});settle(p,150);show_bar(p)
      m=p.evaluate(js(r'''const d=document.getElementById('page-tools');if(!d||!vis(d))return null;
        const a=R(d);const boxes=[...document.querySelectorAll('#main .writing-paper, #main .open-area')].filter(vis).map(R).filter(b=>b.bottom>0&&b.y<innerHeight);
        const hit=boxes.find(b=>a.x<b.right-1&&a.right>b.x+1&&a.y<Math.min(b.bottom,innerHeight)-1&&a.bottom>Math.max(b.y,0)+1);
        return {overlap:!!hit,dock:[Math.round(a.x),Math.round(a.right)],column:hit?[Math.round(hit.x),Math.round(hit.right)]:null};'''))
      if m and m['overlap']: probs.append(f"{w}x{h}: the dock ({m['dock'][0]}-{m['dock'][1]}) covers the content column ({m['column'][0]}-{m['column'][1]})")
      scroll_to(p,0)
    p.set_viewport_size({'width':844,'height':390});settle(p,200);shot(p,'rotation-844x390.png')
  assert not probs,' | '.join(probs[:8])+(f' | ...{len(probs)-8} more' if len(probs)>8 else '')

INSET_SCAN=js(r'''const L=arg.l,Rr=innerWidth-arg.r,B=innerHeight-arg.b,out=[];
for(const sel of arg.regions){const root=document.querySelector(sel);if(!root||!vis(root))continue;const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let bad=0,example='';
 while(w.nextNode()){const n=w.currentNode;if(!n.textContent.trim()||!n.parentElement||n.parentElement.closest('textarea,script,style')||!vis(n.parentElement))continue;const rg=document.createRange();rg.selectNodeContents(n);
  for(const r of rg.getClientRects()){if(!r.width)continue;if(r.left<L-0.5||r.right>Rr+0.5){bad++;example=example||(n.textContent.trim().slice(0,30)+' at '+Math.round(r.left)+'-'+Math.round(r.right));}}}
 for(const e of root.querySelectorAll('textarea,input,select,button')){if(!vis(e))continue;const r=R(e);if(r.x<L-0.5||r.right>Rr+0.5){bad++;example=example||(name(e)+' at '+Math.round(r.x)+'-'+Math.round(r.right));}}
 if(bad)out.push(sel+': '+bad+' text runs or controls inside the side insets, e.g. '+example);}
const t=document.getElementById('page-tools');if(arg.bar&&t&&vis(t)){const r=R(t);if(r.bottom>B+0.5)out.push('#page-tools bottom '+Math.round(r.bottom)+' > '+Math.round(B));}
return out;''')
def simulated_safe_area():
  probs=[]
  inset={'l':59,'r':59,'b':34}
  for w,h in [(390,844),(844,390)]:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      p.evaluate("()=>{const s=document.documentElement.style;s.setProperty('--inset-l','59px');s.setProperty('--inset-r','59px');s.setProperty('--inset-b','34px');dispatchEvent(new Event('resize'));}");settle(p,250)
      probs+=[f'{tag}: {x}' for x in p.evaluate(INSET_SCAN,{**inset,'bar':False,'regions':['.site-header','#main']})]
      # Amendment 2a: the bar hides within 48px of the end, so its clearance is measured 64px before the end; the footer at the end.
      scroll_to(p,p.evaluate('()=>document.documentElement.scrollHeight-innerHeight')-64);settle(p,250)
      if not bar_visible(p): probs.append(tag+': the floating bar is not shown 64px before the end of the page, so its inset clearance cannot be measured')
      probs+=[f'{tag}: {x}' for x in p.evaluate(INSET_SCAN,{**inset,'bar':True,'regions':['#page-tools']})]
      scroll_to(p,10**6);settle(p,250)
      probs+=[f'{tag}: {x}' for x in p.evaluate(INSET_SCAN,{**inset,'bar':False,'regions':['.site-footer']})]
      fb=p.evaluate(js(r'''const f=document.querySelector('.site-footer');if(!f)return null;let max=0;const w=document.createTreeWalker(f,NodeFilter.SHOW_TEXT);while(w.nextNode()){if(!w.currentNode.textContent.trim()||!vis(w.currentNode.parentElement))continue;const rg=document.createRange();rg.selectNodeContents(w.currentNode);for(const r of rg.getClientRects())if(r.width)max=Math.max(max,r.bottom);}return max;'''))
      if fb and fb>h-34+0.5: probs.append(f'{tag}: footer text reaches {fb:.0f}px at the end of the page; the home indicator inset starts at {h-34}px')
      shot(p,f'safe-area-{tag}.png')
      scroll_to(p,0);p.locator('[data-action=about]').first.click();settle(p,300)
      probs+=[f'{tag} reader: {x}' for x in p.evaluate(INSET_SCAN,{**inset,'bar':False,'regions':['#reader']})]
      p.evaluate("()=>{const c=document.getElementById('reader-content');if(c)c.scrollTop=c.scrollHeight;}");settle(p,150)
      rb=p.evaluate(js(r'''const c=document.getElementById('reader-content');if(!c)return null;let max=0;const w=document.createTreeWalker(c,NodeFilter.SHOW_TEXT);while(w.nextNode()){if(!w.currentNode.textContent.trim()||!vis(w.currentNode.parentElement))continue;const rg=document.createRange();rg.selectNodeContents(w.currentNode);for(const r of rg.getClientRects())if(r.width&&r.bottom<=R(c).bottom+1)max=Math.max(max,r.bottom);}return max;'''))
      if rb and rb>h-34+0.5: probs.append(f'{tag} reader: last text line reaches {rb:.0f}px; the bottom inset starts at {h-34}px')
      shot(p,f'safe-area-reader-{tag}.png');close_reader(p)
  assert not probs,' | '.join(probs[:10])+(f' | ...{len(probs)-10} more' if len(probs)>10 else '')

KEYBOARD_SCAN=js(r'''const f=document.activeElement,vh=arg;if(!f||f.tagName!=='TEXTAREA')return {err:'no focused textarea'};
let lab=null;const ids=(f.getAttribute('aria-labelledby')||'').split(/\s+/).filter(Boolean);
if(ids.length)lab=document.getElementById(ids[ids.length-1]);
let lr=null;if(lab)lr=R(lab);else if(f.labels&&f.labels[0]){const l=f.labels[0];const rects=[];const w=document.createTreeWalker(l,NodeFilter.SHOW_TEXT);while(w.nextNode()){const n=w.currentNode;if(!n.textContent.trim()||f.contains(n)||!before(n,f))continue;const rg=document.createRange();rg.selectNodeContents(n);for(const r of rg.getClientRects())if(r.width)rects.push(r);}
 if(rects.length)lr={y:Math.min(...rects.map(r=>r.top)),bottom:Math.max(...rects.map(r=>r.bottom)),x:Math.min(...rects.map(r=>r.left)),right:Math.max(...rects.map(r=>r.right))};}
const cs=getComputedStyle(f),r=R(f),lh=cs.lineHeight==='normal'?parseFloat(cs.fontSize)*1.2:parseFloat(cs.lineHeight);
const top=r.y+parseFloat(cs.borderTopWidth)+parseFloat(cs.paddingTop)-f.scrollTop;const caret={y:top,bottom:top+lh,x:r.x,right:r.right};
const cover=[];for(const el of [document.getElementById('page-tools'),document.getElementById('notice')]){if(!el||!vis(el))continue;const o=R(el);for(const [n,b] of [['label',lr],['caret line',caret]])if(b&&o.x<b.right&&o.right>b.x&&o.y<b.bottom&&o.bottom>b.y)cover.push(el.id+' covers the '+n);}
const up=document.querySelector('[data-fab=up]'),down=document.querySelector('[data-fab=down]');
return {label:lr,caret,vh,keyboard:document.documentElement.dataset.keyboard,arrows:(up&&vis(up))||(down&&vis(down)),cover};''')
def landscape_keyboard():
  probs=[]
  with Session(844,390) as s:
    p=s.open()
    for target in ['#guidance-issue','[data-guide-reply=H]']:
      scroll_to(p,0);p.locator(target).focus();settle(p,200)
      p.evaluate(KEYBOARD_ON,[844,170]);settle(p,500)
      m=p.evaluate(KEYBOARD_SCAN,170)
      if m.get('err'): probs.append(target+': '+m['err'])
      else:
        if m['keyboard']!='true': probs.append(target+': html[data-keyboard] is not "true" with the 844x170 keyboard fixture')
        if m['arrows']: probs.append(target+': Up and Down stay visible above the keyboard')
        if not m['label']: probs.append(target+': no label found for the focused field')
        elif m['label']['y']<-0.5 or m['label']['bottom']>170.5: probs.append(f"{target}: the label is outside the visible 170px (y {m['label']['y']:.0f}-{m['label']['bottom']:.0f})")
        c=m['caret']
        if c['y']<-0.5 or c['bottom']>170.5: probs.append(f"{target}: the caret line is outside the visible 170px (y {c['y']:.0f}-{c['bottom']:.0f})")
        probs+=[target+': '+x for x in m['cover']]
      shot(p,'keyboard-844x170-'+('issue' if target.startswith('#') else 'reply-H')+'.png')
      p.evaluate(KEYBOARD_OFF);p.evaluate('document.activeElement.blur()');settle(p,250)
    if s.calls() or s.writes(): probs.append('focusing fields sent or stored something')
  assert not probs,' | '.join(probs)

def csp_zero_violations():
  if MODE!='http': return 'SKIP DOM mode injects assets without response headers; run in HTTP mode'
  with Session(390,844) as s:
    p=s.open();steps=[]
    assert s.headers.get('content-security-policy')==CSP,'the local server did not send the vercel.json CSP'
    missed=[]
    def step(label,fn,required=True):
      try: fn();settle(p,200);steps.append(label)
      except Exception as e:
        steps.append(label+' (not run: '+type(e).__name__+')')
        if required: missed.append(label+': '+(' '.join(str(e).split())[:120] or type(e).__name__))
    def quick():
      quick_tap(s);forms_filled(p)
    step('quick path',quick,required=p.locator('#quick-pray').count()>0)
    def to_save():
      g=control(p,'#prayer-flow-status','Go to Save');click_id(p,g[0]['id'])
    step('Go to Save',to_save,required=bool(control(p,'#prayer-flow-status','Go to Save')))
    def deeper():
      d=control(p,'#guide-issue',DEEPER);click_id(p,d[0]['id'])
      for k,n in NEXT.items():
        c=control(p,'#reflection-'+k,'Next: '+NAMES[n],whole=True)
        if c: click_id(p,c[0]['id']);settle(p,120)
    step('deep path',deeper,required=bool(control(p,'#guide-issue',DEEPER)))
    def jumps():
      for k in KEYS:
        if p.locator(f'[data-guide-jump={k}]').count(): p.locator(f'[data-guide-jump={k}]').first.click();settle(p,80)
    step('area jumps',jumps,required=p.locator('[data-guide-jump]').count()>0)
    def historic():
      p.locator('[data-guide-action=historic]').first.click();p.locator('#reader').wait_for();close_reader(p)
    step('Read before praying',historic,required=p.locator('[data-guide-action=historic]').count()>0)
    def local_form():
      p.locator('[data-local-form=sentence]').first.click();settle(p,200)  # the replace confirm() is accepted by the dialog handler
    step('Use a local starting prayer',local_form,required=p.locator('[data-local-form=sentence]').count()>0)
    def copy_form():
      p.locator('[data-guide-copy=sentence]').first.click();settle(p,200);dismiss_notice(p)
    step('Copy this prayer',copy_form,required=p.locator('[data-guide-copy=sentence]').count()>0)
    def ai():
      p.locator('#guidance-consent').check();p.locator('#guide-reflect-start').click();p.locator('#guide-understanding').wait_for()
      p.locator('#guidance-confirm').check();p.locator('#guide-prayers-ai').click();wait_js(p,"()=>document.querySelector('[data-prayer-form=sentence]').value.startsWith('TEST FIXTURE')",'AI prayers did not fill')
    step('AI reflection and prayers (fixture)',ai)
    def sizes():
      for size in SIZES:
        set_reading(p,size);close_reader(p)
      assert set_reading(p,'Standard') is None,'no Standard reading size';close_reader(p)
    step('Text size panel',sizes)
    def contents():
      show_bar(p);p.locator('[data-fab=contents]').click();p.locator('#reader').wait_for();close_reader(p);scroll_to(p,0)
    step('Contents',contents)
    for action in ['learn','about','privacy']:
      step(action+' dialog',lambda a=action:(dismiss_notice(p),p.locator(f'[data-action={a}]').first.click(),p.locator('#reader').wait_for(),close_reader(p)))
    def verse():
      p.locator('#reflection-W [data-verse]').first.click();p.locator('#reader iframe.esv-reader-frame').wait_for();settle(p,300);close_reader(p)
    step('Scripture reader',verse)
    def rotate():
      p.set_viewport_size({'width':844,'height':390});settle(p,200);p.set_viewport_size({'width':390,'height':844})
    step('rotation',rotate)
    def download_html():
      dismiss_notice(p)
      with p.expect_download(timeout=6000): p.locator('[data-action=download-html]').first.click()
      dismiss_notice(p)
    step('Download HTML',download_html,required=p.locator('[data-action=download-html]').count()>0)
    def save():
      with s.ctx.expect_page(timeout=6000) as ev: p.locator('[data-action=save]').first.click()
      tab=ev.value;tab.wait_for_load_state('networkidle');settle(tab,300)
      s.tab_csp=tab.evaluate('window.__sp?window.__sp.csp:[]');tab.close()
    s.tab_csp=[]
    step('Save and download tab',save)
    for route in ['scripture','journal']:
      step(route+' route',lambda r=route:nav_to(p,r))
    step('Browse',lambda:(dismiss_notice(p),p.locator('[data-action=browse]').first.click()))
    step('saved entry',lambda:p.locator('[data-action=open-entry]').first.click())
    v=p.evaluate('window.__sp.csp')+s.tab_csp
    found=[f"{x['directive']} blocked {x['blocked'] or 'inline'} ({(x['source'] or '').split('/')[-1]}:{x['line']})" for x in v]+s.console
    (OUT/'csp-steps.json').write_text(json.dumps({'steps':steps,'missed':missed,'violations':found},indent=2))
    assert not found,f'{len(found)} CSP violation(s): '+' | '.join(found[:5])
    assert not missed,'paths that exist could not be exercised: '+' | '.join(missed)
    assert not s.errors,'JavaScript errors: '+' | '.join(s.errors[:3])

BORDERS=js(r'''const b=e=>{if(!e)return 0;const cs=getComputedStyle(e);let m=0;for(const side of ['Top','Right','Bottom','Left'])if(cs['border'+side+'Style']!=='none')m=Math.max(m,parseFloat(cs['border'+side+'Width']));if(cs.outlineStyle!=='none')m=Math.max(m,parseFloat(cs.outlineWidth));return m;};
document.activeElement?.blur();const cur=document.querySelector('.site-header nav a[aria-current]'),other=[...document.querySelectorAll('.site-header nav a:not([aria-current])')];
return {forced:matchMedia('(forced-colors: active)').matches,cur:b(cur),other:Math.max(0,...other.map(b)),hasCur:!!cur};''')
def forced_colors():
  try: s=Session(390,844,forced=True)
  except Exception as e: return f'SKIP forced-colours emulation is not available in {ENGINE}: {type(e).__name__}'
  with s:
    p=s.open()
    m=p.evaluate(BORDERS)
    if not m['forced']: return f'SKIP forced-colours emulation is not available in {ENGINE}'
    probs=[]
    if not m['hasCur']: probs.append('no current nav item (aria-current)')
    elif not (m['cur']>=2 and m['cur']>m['other']): probs.append(f"the current nav item shows no distinct border in forced colours ({m['cur']}px against {m['other']}px)")
    problem=set_reading(p,'Larger')
    if problem: probs.append(problem)
    else:
      t=p.evaluate(js(r'''document.activeElement?.blur();const bs=[...document.querySelectorAll('#reader [data-action=size]')];const words=e=>T(e).replace(/\bChosen\b/g,'').replace(/[()]/g,'').trim();
        const bw=e=>{const cs=getComputedStyle(e);let m=0;for(const s of ['Top','Right','Bottom','Left'])if(cs['border'+s+'Style']!=='none')m=Math.max(m,parseFloat(cs['border'+s+'Width']));if(cs.outlineStyle!=='none')m=Math.max(m,parseFloat(cs.outlineWidth));return m;};
        const c=bs.find(e=>words(e)==='Larger');return {chosen:c?bw(c):0,others:Math.max(0,...bs.filter(e=>e!==c).map(bw)),pressed:c?.getAttribute('aria-pressed'),word:!!c&&/\bChosen\b/.test(T(c))};'''))
      if not (t['chosen']>=2 and t['chosen']>t['others']): probs.append(f"the chosen text size shows no distinct border in forced colours ({t['chosen']}px against {t['others']}px)")
      if t['pressed']!='true': probs.append('the chosen text size lacks aria-pressed="true"')
      if not t['word']: probs.append('the chosen text size does not show "Chosen"')
      shot(p,'forced-colours-text-size.png');close_reader(p)
    shot(p,'forced-colours-390x844.png')
    assert not probs,' | '.join(probs)

def typed_scripts():
  with Session(390,844) as s:
    p=s.open();text='\n'.join(SCRIPTS.values())
    p.locator('#guidance-issue').click()
    for i,part in enumerate(SCRIPTS.values()):
      if i: p.keyboard.press('Enter')
      p.keyboard.insert_text(part)
    probs=[]
    if p.locator('#guidance-issue').input_value()!=text: probs.append('the issue box changed the typed text')
    if p.locator('#quick-pray').count(): p.locator('#quick-pray').click()
    else: p.locator('[data-guide-action=local]').click()
    forms_filled(p)
    ext=p.locator('[data-prayer-form=extended]').input_value()
    for lang,part in SCRIPTS.items():
      if part not in ext: probs.append(lang+' text did not reach the extended prayer intact')
    save_entry(s)
    saved=p.evaluate("()=>JSON.parse(localStorage.getItem('"+JOURNAL_KEY+"')||'{\"entries\":[]}').entries.map(e=>e.journey.issue)")
    if saved!=[text]: probs.append('the saved issue differs from what was typed')
    nav_to(p,'journal');p.locator('[data-action=browse]').first.click();settle(p)
    p.locator('[data-action=open-entry]').first.click();settle(p)
    body=p.locator('#main').inner_text()
    for lang,part in SCRIPTS.items():
      if part not in body: probs.append(lang+' text is not shown on the saved entry')
    p.locator('[data-action=edit]').first.click();settle(p)
    if p.locator('#guidance-issue').input_value()!=text: probs.append('the issue did not round-trip back into the issue box')
    if s.calls(): probs.append('typing sent a request')
    assert not probs,' | '.join(probs)

def quick_path_keeps_whems_in_dom():
  probs=[]
  for w,h in SIMPLE_PATH_SIZES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      if not p.locator('#quick-pray').count(): probs.append(tag+': the quick button "'+QUICK+'" is missing (#quick-pray)');continue
      quick_tap(s)
      try: forms_filled(p)
      except AssertionError as e: probs.append(tag+': '+str(e));continue
      settle(p,300)
      m=p.evaluate(js(r'''const issue=document.getElementById('guide-issue'),pr=document.getElementById('guide-prayers');const areas=[...document.querySelectorAll('section.area.open-area')];
        return {ids:areas.map(a=>a.id),between:areas.every(a=>before(issue,a)&&before(a,pr)),replies:['W','H','E','M','S'].filter(k=>!vis(document.querySelector('[data-guide-reply='+k+']'))),
          choices:['W','H','E','M','S'].flatMap(k=>['thank','ask'].map(t=>[k,t])).filter(([k,t])=>{const i=document.querySelector('[data-field="areas.'+k+'.'+t+'"]');return !i||!vis(i.closest('label')||i);}).map(x=>x.join(' ')),
          whems:document.querySelector('[data-prayer-form=whems]')?.value||''};'''))
      st=p.evaluate(QUICK_RESULT,ISSUE)
      if m['ids']!=['reflection-'+k for k in KEYS]: probs.append(tag+': the five open areas changed: '+', '.join(m['ids']))
      if not m['between']: probs.append(tag+': the areas no longer sit between the issue and the prayers')
      if m['replies']: probs.append(tag+': reply boxes hidden: '+', '.join(m['replies']))
      if m['choices']: probs.append(tag+': thanksgiving or request choices hidden: '+', '.join(m['choices']))
      for k in KEYS:
        if f'{k} - {NAMES[k]}' not in m['whems']: probs.append(f'{tag}: the W.H.E.M.S. prayer lost "{k} - {NAMES[k]}"')
      if st['differs']: probs.append(tag+': the quick path is not the local branch: '+', '.join(st['differs'])+' differ from WholeheartedGuidance.local(draft)')
      if not (450<=st['extendedWords']<=900) or not st['extendedHasIssue']: probs.append(f"{tag}: the extended prayer breaks the local contract ({st['extendedWords']} words, issue present: {st['extendedHasIssue']})")
      d=control(p,'#guide-issue',DEEPER)
      if not d or not d[0]['visible']: probs.append(tag+': "'+DEEPER+'" is no longer offered after the quick prayers')
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

def choose_voice(p,value):
  v=p.locator('[data-guide-voice]')
  if not v.count(): return 'no [data-guide-voice] control'
  if v.first.evaluate('e=>e.tagName')=='SELECT': v.first.select_option(value)
  else: p.locator(f'[data-guide-voice][value={value}]').check()
  return None
def quick_sends_nothing():
  probs=[]
  with Session(390,844) as s:
    p=s.open();s.mark();stored=storage_state(p)
    if not p.locator('#quick-pray').count(): probs.append('the quick button "'+QUICK+'" is missing (#quick-pray)')
    else:
      p.locator('#guidance-issue').click();p.keyboard.type('Should I move closer to my mother?')
      p.locator('[data-journey=context]').fill('She lives alone. I have not asked her yet.')
      for k in KEYS: p.locator(f'[data-guide-reply={k}]').fill(f'My own words for {NAMES[k]}.')
      p.locator('[data-field="areas.W.thank"]').check();p.locator('[data-field="areas.E.ask"]').check()
      voice=choose_voice(p,'community')
      if voice: probs.append('full draft: '+voice)
      p.set_viewport_size({'width':844,'height':390});settle(p,200);p.set_viewport_size({'width':390,'height':844});settle(p,200)
      quick_tap(s,None);forms_filled(p);settle(p,300)
      g=control(p,'#prayer-flow-status','Go to Save')
      if g: click_id(p,g[0]['id']);settle(p,300)
      st=p.evaluate("()=>({sp:window.__sp||{},cookie:(()=>{try{return document.cookie;}catch(e){return '';}})(),consent:!!document.getElementById('guidance-consent')?.checked,confirm:!!document.getElementById('guidance-confirm')?.checked})")
      if s.calls(): probs.append(f'full draft: {s.calls()} /api/guidance request(s)')
      if s.since(): probs.append('full draft: network request(s): '+', '.join(s.since()[:3]))
      if s.blocked: probs.append('full draft: attempted external request(s): '+', '.join(s.blocked[:3]))
      if s.writes(): probs.append(f'full draft: {s.writes()} storage write(s)')
      if stored is not None and storage_state(p)!=stored: probs.append('full draft: browser storage changed')
      sp=st['sp']
      if sp.get('sessionWrites') or sp.get('idb') or sp.get('beacons'): probs.append('full draft: session storage, IndexedDB or a beacon was used')
      if st['cookie']: probs.append('full draft: a cookie was set')
      if not st['consent'] or st['confirm']: probs.append('full draft: the consent box lost its default tick, or the acknowledgement was ticked (A28)')
  # With consent ticked, the quick path must still take the local branch and send nothing.
  with Session(390,844) as s:
    p=s.open()
    if p.locator('#quick-pray').count():
      p.locator('#guidance-consent').check();settle(p,150);s.mark();quick_tap(s)
      try:
        forms_filled(p);settle(p,300)
        st=p.evaluate(QUICK_RESULT,ISSUE)
        if s.calls(): probs.append(f'consent ticked: {s.calls()} /api/guidance request(s); the quick path must never send')
        if s.since(): probs.append('consent ticked: network request(s): '+', '.join(s.since()[:3]))
        if 'Nothing was sent' not in st['status']: probs.append('consent ticked: #prayer-flow-status does not say "Nothing was sent"')
        if st['feedback']: probs.append('consent ticked: validation feedback appeared')
        if st['differs']: probs.append('consent ticked: the quick path did not fill the local prayers')
        if p.locator('#guidance-confirm').count() and p.locator('#guidance-confirm').is_checked(): probs.append('consent ticked: the acknowledgement was ticked')
        if s.writes() or s.dialogs: probs.append('consent ticked: stored or raised a dialog')
      except AssertionError as e: probs.append('consent ticked: '+str(e))
  # After an AI reflection, the quick path still bypasses the summary gate and sends nothing new (I2, I4).
  with Session(390,844) as s:
    p=s.open()
    if p.locator('#quick-pray').count():
      fill_issue(p);p.locator('#guidance-consent').check();p.locator('#guide-reflect-start').click()
      try: p.locator('#guide-understanding').wait_for();settle(p,300)
      except PWTimeout: probs.append('after reflection: the reflection fixture did not render #guide-understanding')
      else:
        s.mark();calls=s.calls();quick_tap(s,None)
        try:
          forms_filled(p);settle(p,300)
          st=p.evaluate(QUICK_RESULT,ISSUE)
          if s.calls()!=calls: probs.append(f'after reflection: the quick tap sent {s.calls()-calls} request(s)')
          if s.since(): probs.append('after reflection: network request(s): '+', '.join(s.since()[:3]))
          if st['feedback']: probs.append('after reflection: a summary or consent gate appeared on the quick path')
          if p.locator('#guidance-confirm').is_checked(): probs.append('after reflection: the understanding acknowledgement was ticked')
          if 'Nothing was sent' not in st['status']: probs.append('after reflection: #prayer-flow-status does not say "Nothing was sent"')
          if st['differs']: probs.append('after reflection: the quick path did not fill the local prayers')
          if s.writes() or s.dialogs: probs.append('after reflection: stored or raised a dialog')
        except AssertionError as e: probs.append('after reflection: '+str(e))
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

# ---------- Amendment 1 ----------
CYCLE_POS=js(r'''const t=document.activeElement;if(!t||t.tagName!=='TEXTAREA')return {err:'no focused textarea'};
const cs=getComputedStyle(t),r=R(t),lh=cs.lineHeight==='normal'?parseFloat(cs.fontSize)*1.2:parseFloat(cs.lineHeight);
const lines=t.value.split('\n').length;const caretTop=r.y+parseFloat(cs.borderTopWidth)+parseFloat(cs.paddingTop)+(lines-1)*lh-t.scrollTop,caretBottom=caretTop+lh;
/* A phone browser keeps the caret just above the keyboard: put the caret line at the bottom of the visual viewport. */
const vh=arg;const by=caretBottom-(vh-8);const beforeY=scrollY;
if(Math.abs(by)>0.5)window.__sp.scrollBy({top:by,left:0,behavior:'instant'});
const moved=scrollY-beforeY;return {scrollY,caretTop:caretTop-moved,caretBottom:caretBottom-moved};''')
LANDING=js(r'''const t=document.querySelector('[data-prayer-form=sentence]'),h=document.querySelector('#prayer-sentence h3');if(!t)return {missing:true};const r=R(t);
return {top:r.y,bottom:r.y+r.height,h:innerHeight,len:t.value.trim().length,headingY:h?R(h).y:null,focus:name(document.activeElement)};''')
def quick_lands_on_prayer():
  # Amendment 3 (I24, A29): after the quick tap the first prayer's words are on the screen, not a second row of buttons.
  probs=[]
  for w,h in ((390,844),(320,568),(844,390)):
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';quick_tap(s)
      try: forms_filled(p)
      except AssertionError as e: probs.append(tag+': '+str(e));continue
      settle(p,500);m=p.evaluate(LANDING);shot(p,f'landing-{tag}.png')
      if m.get('missing'): probs.append(tag+': the sentence prayer box is missing');continue
      if not (0<=m['top']<m['h']): probs.append(f"{tag}: the sentence prayer box starts at {m['top']:.0f}px; the screen is {m['h']}px")
      if m['len']<50: probs.append(f"{tag}: the sentence prayer holds only {m['len']} characters")
      if m['headingY'] is None or m['headingY']<-1: probs.append(tag+': the first prayer heading is above the screen')
      if s.dialogs: probs.append(tag+': dialog: '+s.dialogs[0])
  assert not probs,' | '.join(probs)

def replace_only_when_edited():
  # Amendment 3 (I25, A30): the app's own unedited drafts are replaced without a question; edited words get the question, and Cancel keeps them.
  probs=[]
  with Session(390,844) as s:
    p=s.open();s.mark();quick_tap(s);forms_filled(p);settle(p,1000)   # past the 900ms same-tap guard
    p.evaluate("()=>{window.__asked=[];window.__answer=false;window.confirm=m=>{window.__asked.push(m);return window.__answer;};}")
    scroll_to(p,0);settle(p,200);p.locator('[data-guide-action=local]').click();settle(p,600)
    m=p.evaluate(LANDING);asked=p.evaluate('()=>window.__asked.length')
    if asked: probs.append(f'unedited drafts: the in-section button asked {asked} question(s)')
    if not (0<=m['top']<m['h']): probs.append(f"unedited drafts: the page did not land on the first prayer (box top {m['top']:.0f}px)")
    mine='My own words, kept as they are.'
    p.locator('[data-prayer-form=sentence]').fill(mine);settle(p,200)
    scroll_to(p,0);settle(p,200);p.locator('[data-guide-action=local]').click();settle(p,600)
    asked=p.evaluate('()=>window.__asked.length');m=p.evaluate(LANDING)
    if asked!=1: probs.append(f'edited prayer: expected one question, got {asked}')
    if p.locator('[data-prayer-form=sentence]').input_value()!=mine: probs.append('edited prayer: Cancel did not keep the edited words')
    if not (0<=m['top']<m['h']): probs.append(f"edited prayer, Cancel: the page did not land on the first prayer (box top {m['top']:.0f}px)")
    p.evaluate('()=>{window.__answer=true;}');p.locator('[data-guide-action=local]').click();settle(p,600)
    asked=p.evaluate('()=>window.__asked.length')
    if asked!=2: probs.append(f'edited prayer, Yes: expected a second question, got {asked}')
    if p.locator('[data-prayer-form=sentence]').input_value()==mine: probs.append('edited prayer, Yes: the prayer was not replaced')
    if s.calls() or s.since(): probs.append('something was sent')
    if s.dialogs: probs.append('a native dialog appeared: '+s.dialogs[0])
  assert not probs,' | '.join(probs)

def typing_no_jump():
  probs=[]
  with Session(390,844) as s:
    p=s.open()
    reply=p.locator('[data-guide-reply=H]');reply.fill('\n'.join(f'Line {i+1}, listening.' for i in range(14)))
    p.evaluate("()=>{const t=document.querySelector('[data-guide-reply=H]');t.scrollIntoView({block:'center'});t.focus({preventScroll:true});t.setSelectionRange(t.value.length,t.value.length);}")
    settle(p,300);p.evaluate(KEYBOARD_ON,[390,340]);settle(p,700)  # one adjustment after focus or a viewport resize is allowed (I19)
    if p.evaluate("()=>document.documentElement.dataset.keyboard")!='true': probs.append('html[data-keyboard] is not "true" with the 390x340 keyboard fixture')
    p.evaluate("()=>{window.__sp.scrolls.length=0;}")
    cycles=[]
    for i in range(10):
      pos=p.evaluate(CYCLE_POS,340)
      if pos.get('err'): probs.append(pos['err']);break
      if pos['caretBottom']>340.5: probs.append(f"cycle {i+1}: the caret line could not be placed above the keyboard (ends at {pos['caretBottom']:.0f}px of 340); the page is too short below the Heart reply");break
      settle(p,140)
      y0=p.evaluate('scrollY')
      if abs(y0-pos['scrollY'])>1: probs.append(f"cycle {i+1}: the app scrolled from {pos['scrollY']:.0f} to {y0:.0f} after the browser brought the caret into view");break
      p.keyboard.type('a');settle(p,160)
      y1=p.evaluate('scrollY');calls=p.evaluate('window.__sp.scrolls.map(s=>s.fn+(s.top!==undefined?" "+Math.round(s.top):""))')
      cycles.append({'positioned':pos['scrollY'],'afterKey':y1,'appScrolls':calls})
      if abs(y1-y0)>1: probs.append(f'cycle {i+1}: typing one character moved the page from {y0:.0f} to {y1:.0f} (the typing jump)');break
      if calls: probs.append(f'cycle {i+1}: the app scrolled in answer to typing: '+', '.join(calls[:3]));break
    (OUT/'typing-no-jump.json').write_text(json.dumps(cycles,indent=1))
    p.evaluate(KEYBOARD_OFF)
    if s.calls() or s.writes(): probs.append('typing sent or stored something')
  assert not probs,' | '.join(probs)

BAR_STATE=js(r'''const t=document.getElementById('page-tools');if(!t||!vis(t))return {visible:false,buttons:[]};
return {visible:true,buttons:[...t.querySelectorAll('button')].filter(vis).map(e=>({fab:e.dataset.fab||'',w:R(e).w,h:R(e).h})),rect:R(t)};''')
def bar_hidden_while_typing():
  probs=[]
  with Session(390,844) as s:
    p=s.open()
    if not show_bar(p): probs.append('the floating bar is not shown after scrolling three screens, so its keyboard behaviour cannot be checked (see bar_after_two_screens)')
    else:
      p.evaluate("()=>{const t=document.querySelector('[data-guide-reply=S]');t.scrollIntoView({block:'center'});t.focus({preventScroll:true});}");settle(p,300)
      if p.evaluate('scrollY')<=2*844: probs.append('the Soul reply box is within two screens of the top, so the bar is not expected there; the check needs a longer page')
      elif not bar_visible(p): probs.append('the bar disappeared when the Soul reply box was focused, before any keyboard')
      else:
        p.evaluate(KEYBOARD_ON,[390,340])
        try: wait_js(p,js("return document.documentElement.dataset.keyboard==='true'&&!vis(document.getElementById('page-tools'));"),'x',timeout=800)
        except AssertionError:
          st=p.evaluate("()=>document.documentElement.dataset.keyboard")
          probs.append('the bar stays visible while the keyboard is open (data-keyboard='+str(st)+')')
        t0=time.monotonic();p.evaluate(KEYBOARD_OFF)
        try: wait_js(p,js("return vis(document.getElementById('page-tools'));"),'x',timeout=1200)
        except AssertionError: probs.append('the bar did not come back after the keyboard closed')
        else:
          back=(time.monotonic()-t0)*1000
          if back>330: probs.append(f'the bar came back {back:.0f}ms after the keyboard closed; 300ms allowed')
        shot(p,'bar-after-keyboard-390x844.png')
    if s.calls() or s.writes(): probs.append('focusing a field sent or stored something')
  assert not probs,' | '.join(probs)

def bar_after_two_screens():
  probs=[]
  for w,h in [(390,844),(844,390)]:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}'
      for y in [0,h,2*h]:
        scroll_to(p,y);settle(p,160)
        if bar_visible(p): probs.append(f'{tag}: the bar shows at scrollY {y} (within two screens)')
      for y in [2*h+40,3*h]:
        scroll_to(p,y);settle(p,160)
        if not bar_visible(p): probs.append(f'{tag}: the bar is absent at scrollY {y} (beyond two screens)')
      shot(p,f'bar-{tag}.png')
  assert not probs,' | '.join(probs)

def bar_phone_single_button():
  probs=[]
  for w,h,single in [(390,844,True),(320,568,True),(667,375,True),(768,1024,False),(1024,768,False),(844,390,False)]:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';show_bar(p);m=p.evaluate(BAR_STATE)
      if not m['visible']: probs.append(tag+': the bar is not shown beyond two screens');continue
      fabs=[b['fab'] for b in m['buttons']]
      if single:
        if fabs!=['contents']: probs.append(f'{tag}: below 700px wide the bar must hold one Contents button only; visible: {fabs}')
        c=[b for b in m['buttons'] if b['fab']=='contents']
        if c and (c[0]['w']<47.5 or c[0]['h']<47.5): probs.append(f"{tag}: the Contents button is {c[0]['w']:.0f}x{c[0]['h']:.0f}; 48x48 needed")
      else:
        if sorted(fabs)!=['contents','down','up']: probs.append(f'{tag}: at 768px and wider the bar keeps Contents, Up and Down; visible: {fabs}')
        for b in m['buttons']:
          if b['w']<47.5 or b['h']<47.5: probs.append(f"{tag}: {b['fab']} is {b['w']:.0f}x{b['h']:.0f}; 48x48 needed")
  assert not probs,' | '.join(probs)

HEADER_SCAN=js(r'''const h=document.querySelector('.site-header');if(!h)return null;const brand=h.querySelector('.brand'),aa=h.querySelector('[data-action=text-size]');
return {height:R(h).h,brand:brand&&vis(brand)?R(brand).h:null,tabs:[...h.querySelectorAll('nav a')].filter(vis).map(e=>({t:W(e),h:R(e).h})),aa:aa&&vis(aa)?R(aa).h:null,overflow:document.documentElement.scrollWidth-innerWidth};''')
def header_height():
  probs=[]
  for w,h in PORTRAIT:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';m=p.evaluate(HEADER_SCAN)
      if not m: probs.append(tag+': .site-header missing');continue
      limit=112 if w<=320 else 72
      if m['height']>limit+0.5: probs.append(f"{tag}: the header is {m['height']:.0f}px tall; at most {limit}px")
      if m['brand'] is None or m['brand']<31.5: probs.append(f"{tag}: the brand link is {m['brand']}px tall; at least 32px")
      if len(m['tabs'])<3: probs.append(f"{tag}: {len(m['tabs'])} visible nav tabs; Pray, Journal and Scripture expected")
      for t in m['tabs']:
        if t['h']<39.5: probs.append(f"{tag}: tab \"{t['t']}\" is {t['h']:.0f}px tall; at least 40px")
      if m['aa'] is None or m['aa']<39.5: probs.append(f"{tag}: the Aa button is {m['aa']}px tall; at least 40px")
      if m['overflow']>1: probs.append(f"{tag}: the page overflows by {m['overflow']}px")
  assert not probs,' | '.join(probs[:12])+(f' | ...{len(probs)-12} more' if len(probs)>12 else '')

DENSITY=js(r'''const header=document.querySelector('.site-header');const top=header?Math.max(0,R(header).bottom):0;const H=innerHeight;const rows=new Uint8Array(Math.max(0,Math.ceil(H-top)));
const mark=(a,b)=>{const s=Math.max(top,a),e=Math.min(H,b);for(let y=Math.floor(s-top);y<Math.ceil(e-top);y++)if(y>=0&&y<rows.length)rows[y]=1;};
for(const e of document.querySelectorAll('body *')){if(e.closest('.site-header,#page-tools,#notice,dialog,script,style,noscript')||!vis(e))continue;const r=e.getBoundingClientRect();if(r.bottom<=top||r.top>=H)continue;
 if(e.matches('input,textarea,select,button,summary')||(e.children.length===0&&e.textContent.trim())){mark(r.top,r.bottom);continue;}
 for(const n of e.childNodes){if(n.nodeType!==3||!n.textContent.trim())continue;const rg=document.createRange();rg.selectNodeContents(n);for(const q of rg.getClientRects())if(q.width>0&&q.height>0)mark(q.top,q.bottom);}}
let covered=0;for(const v of rows)covered+=v;return {covered,total:rows.length,ratio:rows.length?covered/rows.length:0,headerBottom:top};''')
def first_screen_density():
  probs=[];seen=[]
  for w,h in [(430,932),(393,852),(375,667)]:
    with Session(w,h) as s:
      p=s.open();m=p.evaluate(DENSITY);seen.append(f"{w}x{h} {m['ratio']:.0%}")
      if m['ratio']<0.85: probs.append(f"{w}x{h}: {m['ratio']:.0%} of the {m['total']} rows below the header ({m['headerBottom']:.0f}px) hold text or controls; at least 85% needed")
      shot(p,f'density-{w}x{h}.png')
  assert not probs,' | '.join(probs)
  return 'NOTE first-screen density: '+', '.join(seen)

def line_spacing():
  with Session(390,844) as s:
    p=s.open()
    m=p.evaluate(js(r'''const b=getComputedStyle(document.body);const bf=parseFloat(b.fontSize),bl=b.lineHeight==='normal'?NaN:parseFloat(b.lineHeight);
      const paras=[...document.querySelectorAll('#main p')].filter(vis).map(e=>{const cs=getComputedStyle(e);return {t:W(e).slice(0,40),fs:parseFloat(cs.fontSize),lh:cs.lineHeight==='normal'?NaN:parseFloat(cs.lineHeight)};});
      return {bf,bl,paras};'''))
    probs=[]
    if abs(m['bf']-20)>0.25: probs.append(f"body text is {m['bf']}px; 20px expected")
    ratio=m['bl']/m['bf'] if m['bl'] else float('nan')
    if not (1.43<=ratio<=1.47): probs.append(f"body line-height / font-size is {ratio:.3f}; 1.45 (+/-0.02) expected")
    bad=[f"{x['t']!r} {x['lh']/x['fs']:.2f}" for x in m['paras'] if abs(x['fs']-20)<=0.25 and not (x['lh'] and 1.43<=x['lh']/x['fs']<=1.47)]
    if bad: probs.append(f'{len(bad)} body paragraph(s) off 1.45, e.g. '+'; '.join(bad[:3]))
    assert not probs,' | '.join(probs)
    return f'NOTE body line spacing {ratio:.3f} over {len(m["paras"])} visible paragraphs'

LOOK_SCAN=js(ACCENT_NAMES+r'''accentNames.delete('--action');const gilt=new Set([...accentNames].map(n=>probe('var('+n+')')));gilt.delete('rgba(0, 0, 0, 0)');
const probs=[],seen=new Set();
for(const sel of arg){for(const root of document.querySelectorAll(sel)){for(const e of [root,...root.querySelectorAll('*')]){if(seen.has(e)||!vis(e))continue;seen.add(e);
 if(e.matches('svg,img,picture,canvas'))probs.push(name(e)+' inside '+sel);
 const cs=getComputedStyle(e);
 for(const prop of ['backgroundImage','borderImageSource','maskImage','webkitMaskImage','listStyleImage'])if(cs[prop]&&cs[prop]!=='none')probs.push(name(e)+' inside '+sel+' has '+prop+' '+cs[prop].slice(0,40));
 for(const ps of ['::before','::after']){const c=getComputedStyle(e,ps).content;if(c&&c!=='none'&&c!=='normal'&&(/url\(/.test(c)||CROSS.test(c)))probs.push(name(e)+ps+' inside '+sel+' draws '+c.slice(0,30));}
 const cols=[['color',cs.color],['background',cs.backgroundColor]];if(cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>0)cols.push(['outline',cs.outlineColor]);
 for(const side of ['Top','Right','Bottom','Left'])if(cs['border'+side+'Style']!=='none'&&parseFloat(cs['border'+side+'Width'])>0)cols.push(['border-'+side.toLowerCase(),cs['border'+side+'Color']]);
 for(const [what,v] of cols)if(gilt.has(v))probs.push(name(e)+' inside '+sel+' uses gilt for '+what);
}}}
if(gilt.has(probe('var(--line)')))probs.push('--line resolves to a gilt colour');
return probs;''')
def look_rules():
  with Session(390,844) as s:
    p=s.open();probs=[]
    if p.locator('#quick-pray').count(): quick_tap(s);forms_filled(p);settle(p,300)
    probs+=p.evaluate(LOOK_SCAN,['#guide-prayers','#prayer-flow-status','#ai-state','#guide-consent','#guide-options'])
    fill_issue(p);p.locator('#guidance-consent').check();p.locator('#guide-reflect-start').click();p.locator('#guide-understanding').wait_for();settle(p,300)
    probs+=p.evaluate(LOOK_SCAN,['#guide-understanding-slot','#guide-options']+[f'#question-{k}' for k in KEYS]+[f'#reply-label-{k}' for k in KEYS]+['[data-context-focus]','[data-context-followup]','[data-context-references]'])
    probs=list(dict.fromkeys(probs))
    assert not probs,f'{len(probs)} ornament(s) on prayer or AI containers: '+' | '.join(probs[:8])+(f' | ...{len(probs)-8} more' if len(probs)>8 else '')

CHECKS=[first_screen,quick_issue_only,quick_blank_issue,quick_double_tap,go_to_save,ai_quick_path,deep_path_navigation,one_primary_per_screen,save_promise_line,
  safety_list,matrix_no_overflow,tap_targets,min_font,rotation,simulated_safe_area,landscape_keyboard,csp_zero_violations,forced_colors,typed_scripts,
  quick_path_keeps_whems_in_dom,quick_sends_nothing,typing_no_jump,bar_hidden_while_typing,bar_after_two_screens,bar_phone_single_button,quick_lands_on_prayer,replace_only_when_edited,header_height,first_screen_density,line_spacing,look_rules]

results=[]
def run(fn):
  name=fn.__name__
  if ONLY and name not in ONLY: return
  t=time.monotonic();status,reason='PASS',''
  try:
    r=fn()
    if isinstance(r,str) and r.startswith('SKIP'): status,reason='SKIP',r[5:]
    elif isinstance(r,str) and r.startswith('NOTE'): reason=r[5:]
  except AssertionError as e: status,reason='FAIL',str(e) or 'assertion failed'
  except PWTimeout as e: status,reason='ERROR','Playwright timeout: '+str(e).splitlines()[0]
  except Exception as e: status,reason='ERROR',f'{type(e).__name__}: '+str(e).splitlines()[0] if str(e) else type(e).__name__
  line=' '.join(reason.split())
  print(f'{status} {name}'+(f' - {line[:700]}' if line else ''),flush=True)
  results.append({'check':name,'result':status,'reason':reason,'seconds':round(time.monotonic()-t,1)})

unknown=ONLY-{f.__name__ for f in CHECKS}
if unknown: sys.exit('unknown check(s) in SIMPLE_PATH_CHECKS: '+', '.join(sorted(unknown)))
fresh_build()
server=None;URL='https://fixture.invalid/'
if MODE=='http':
  server=QuietServer(('127.0.0.1',0),VercelHeaders);threading.Thread(target=server.serve_forever,daemon=True).start()
  URL=f'http://127.0.0.1:{server.server_address[1]}/'
try:
  with sync_playwright() as pw:
    kwargs={'args':['--no-sandbox']} if ENGINE=='chromium' else {}
    if ENGINE=='chromium':
      if os.environ.get('CHROMIUM_PATH'): kwargs['executable_path']=os.environ['CHROMIUM_PATH']
      elif MODE=='dom': kwargs['executable_path']='/usr/bin/chromium'
    browser=getattr(pw,ENGINE).launch(**kwargs)
    for fn in CHECKS: run(fn)
    browser.close()
finally:
  if server: server.shutdown()
  (OUT/f'simple-path-{MODE}-{ENGINE}-results.json').write_text(json.dumps({'mode':MODE,'engine':ENGINE,'ai':'Labelled fixtures; external requests aborted','keyboard':'visualViewport geometry fixture, not a device keyboard','safe_area':'CSS custom-property injection, not a device notch','sizes':SIMPLE_PATH_SIZES,'results':results},indent=2,ensure_ascii=False))
failed=[r for r in results if r['result'] in ('FAIL','ERROR')]
print(f"{sum(r['result']=='PASS' for r in results)} passed, {len(failed)} failed, {sum(r['result']=='SKIP' for r in results)} skipped",flush=True)
sys.exit(1 if failed or not results else 0)
