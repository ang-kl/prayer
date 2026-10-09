#!/usr/bin/env python3
"""Scroll stability on phones (spec Amendment 2, 2a): the page never moves by itself.

Checks: no_dynamic_units, toolbar_no_shift, tap_no_jump, fab_round, fab_hidden_near_end, fab_hidden_while_scrolling.
Run: node build.cjs && EVIDENCE_DIR=<folder> CHROMIUM_PATH=<chrome> python tests/scroll-stability-browser.py
Env: TEST_BROWSER=chromium|webkit, SCROLL_CHECKS (comma-separated subset). HTTP mode only, served with the
vercel.json headers. The keyboard and toolbar fixtures are viewport models, not a device keyboard or Safari.
"""
import json, os, re, sys, threading, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
OUT=Path(os.environ.get('EVIDENCE_DIR', str(ROOT/'evidence')))/'scroll-stability'
OUT.mkdir(parents=True,exist_ok=True)
ENGINE=os.environ.get('TEST_BROWSER','chromium')
ONLY={x.strip() for x in os.environ.get('SCROLL_CHECKS','').split(',') if x.strip()}
PHONES=[(390,844),(320,568)]

def vercel_headers():
  cfg=json.loads((ROOT/'vercel.json').read_text())
  out=[(h['key'],h['value']) for rule in cfg.get('headers',[]) if rule.get('source')=='/(.*)' for h in rule.get('headers',[])]
  assert any(k=='Content-Security-Policy' for k,_ in out),'vercel.json no longer sets a CSP for every path'
  return out
HEADERS=vercel_headers()

def fresh_build():
  src=(ROOT/'build.cjs').read_text();m=re.search(r"const assets=\[([^\]]*)\]",src)
  assets=re.findall(r"'([^']+)'",m.group(1)) if m else []
  theme=re.search(r"const css=`([^`]*)`",(ROOT/'theme.js').read_text())
  if not assets or not theme: sys.exit('build.cjs or theme.js changed shape; the freshness check cannot read the asset list')
  stale=[f for f in assets if not (PUBLIC/f).exists() or (PUBLIC/f).read_bytes()!=((theme.group(1)+'\n').encode()+(ROOT/f).read_bytes() if f=='styles.css' else (ROOT/f).read_bytes())]
  if stale: sys.exit('public/ is missing or stale ('+', '.join(stale)+'): run `node build.cjs` first.')

class VercelHeaders(SimpleHTTPRequestHandler):
  extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.html':'text/html; charset=utf-8','.json':'application/json'}
  def __init__(self,*a,**k): super().__init__(*a,directory=str(PUBLIC),**k)
  def end_headers(self):
    for k,v in HEADERS: self.send_header(k,v)
    self.send_header('Cache-Control','no-store');super().end_headers()
  def log_message(self,*a): pass
class QuietServer(ThreadingHTTPServer):
  daemon_threads=True
  def handle_error(self,request,client_address): pass

# Records every scroll the app makes. The test's own moves run with __mine set, so they are not counted.
INIT_JS=r'''(()=>{if(window.__ss)return;const ss=window.__ss={scrolls:[],mine:false,t0:performance.now()};
const to=window.scrollTo.bind(window),by=window.scrollBy.bind(window),sc=window.scroll.bind(window);ss.scrollTo=to;
const rec=(fn,a)=>{if(ss.mine)return;const o=a[0]&&typeof a[0]==='object'?a[0]:{top:a[1]};ss.scrolls.push({fn,top:o.top,at:Math.round(performance.now()-ss.t0),y:scrollY});};
window.scrollTo=function(...a){rec('scrollTo',a);return to(...a);};window.scrollBy=function(...a){rec('scrollBy',a);return by(...a);};window.scroll=function(...a){rec('scroll',a);return sc(...a);};
const siv=Element.prototype.scrollIntoView;Element.prototype.scrollIntoView=function(...a){if(!ss.mine)ss.scrolls.push({fn:'scrollIntoView',at:Math.round(performance.now()-ss.t0),y:scrollY});return siv.apply(this,a);};})();'''
H=r'''const vis=e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none';
const R=e=>{const r=e.getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height,bottom:r.bottom};};
const W=e=>{const c=e.cloneNode(true);c.querySelectorAll('[aria-hidden=true]').forEach(x=>x.remove());return (c.textContent||'').replace(/\s+/g,' ').trim();};
const mine=f=>{window.__ss.mine=true;try{return f();}finally{window.__ss.mine=false;}};
const go=y=>mine(()=>{window.__ss.scrollTo({top:y,left:0,behavior:'instant'});return scrollY;});
const extent=()=>document.documentElement.scrollHeight-innerHeight;
'''
def js(body): return '(arg)=>{'+H+body+'}'
KEYBOARD_ON="""(g)=>{window.__realVV=window.__realVV||window.visualViewport;Object.defineProperty(window,'visualViewport',{configurable:true,value:{width:g[0],height:g[1],offsetTop:0,offsetLeft:0,scale:1,addEventListener(){},removeEventListener(){}}});dispatchEvent(new Event('resize'));}"""
KEYBOARD_OFF="""()=>{Object.defineProperty(window,'visualViewport',{configurable:true,value:window.__realVV});dispatchEvent(new Event('resize'));}"""

class Session:
  def __init__(self,w,h):
    self.ctx=browser.new_context(viewport={'width':w,'height':h});self.ctx.add_init_script(INIT_JS)
    self.ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(URL) else r.abort())
    self.page=self.ctx.new_page();self.page.set_default_timeout(6000)
  def open(self):
    p=self.page;p.goto(URL+'#pray',wait_until='networkidle');p.wait_for_selector('#main h1',state='attached');p.wait_for_timeout(200);return p
  def __enter__(self): return self
  def __exit__(self,*a):
    try: self.ctx.close()
    except Exception: pass

def settle(p,ms=220): p.wait_for_timeout(ms)
def scroll_to(p,y): return p.evaluate(js('return go(arg);'),y)
def app_scrolls(p): return p.evaluate('window.__ss.scrolls')
def clear_scrolls(p): p.evaluate('window.__ss.scrolls.length=0')
def bar_state(p): return p.evaluate(js("const t=document.getElementById('page-tools');if(!t||!vis(t))return {visible:false};const b=[...t.querySelectorAll('button')].filter(vis);return {visible:true,buttons:b.map(e=>({fab:e.dataset.fab||'',w:R(e).w,h:R(e).h,words:W(e),label:e.getAttribute('aria-label')||''}))};"))
def bar_visible(p): return bar_state(p)['visible']
def shot(p,name):
  try: p.screenshot(path=str(OUT/name))
  except Exception: pass
def long_reply(p,key='H',lines=20): p.locator(f'[data-guide-reply={key}]').fill('\n'.join(f'Line {i+1}, listening.' for i in range(lines)))

# ---------- checks ----------
ALLOWED=re.compile(r'(^|[\s,>])(dialog|#reader|\.reader-|html\.reader-open|#notice|\.page-tools|\.inline-status|@page)')
def no_dynamic_units():
  """In-flow elements never size themselves with units that change while the page scrolls (I21)."""
  probs=[]
  for name in ['styles.css','experience.css']:
    css=re.sub(r'/\*.*?\*/','',(PUBLIC/name).read_text(),flags=re.S)
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}',css):
      sel,body=m.group(1).strip(),m.group(2)
      if sel.startswith('@') and '{' not in body: continue
      for decl in body.split(';'):
        if ':' not in decl: continue
        prop,val=[x.strip() for x in decl.split(':',1)]
        if prop.startswith('--'): continue
        if not re.search(r'(^|[\s(])(?:max-|min-)?(?:height|width)$|^(?:inset|top|bottom)$',prop): continue
        if re.search(r'\d(?:d|s|l)?vh\b|var\(--vp-height\)',val) and not ALLOWED.search(' '+sel):
          probs.append(f'{name}: {sel[:60]} {{{prop}:{val}}}')
  assert not probs,'viewport-height sizing on in-flow elements: '+' | '.join(probs[:8])

def toolbar_no_shift():
  """A focused reply box keeps its height and the app never scrolls when innerHeight shrinks by 60px in three steps (the toolbar model)."""
  probs=[]
  with Session(390,844) as s:
    p=s.open();long_reply(p);p.locator('[data-guide-reply=H]').focus();settle(p,500)
    heights=lambda:p.evaluate("()=>[...document.querySelectorAll('textarea')].map(t=>Math.round(t.getBoundingClientRect().height))")
    h0=heights();y0=p.evaluate('scrollY');clear_scrolls(p)
    for h in (824,804,784):
      p.set_viewport_size({'width':390,'height':h});settle(p,200)
    settle(p,600)
    h1=heights();calls=app_scrolls(p)
    if h0!=h1: probs.append(f'textarea heights changed with the viewport height: {h0} -> {h1}')
    if calls: probs.append('the app scrolled during a height-only viewport change: '+json.dumps(calls[:3]))
    if abs(p.evaluate('scrollY')-y0)>1: probs.append(f'the page moved from {y0} to {p.evaluate("scrollY")}')
    shot(p,'toolbar-model-390x784.png')
  assert not probs,' | '.join(probs)

def tap_no_jump():
  """Tapping a box then a five-step keyboard animation: at most one app scroll, no earlier than 400ms after the last step, and none when the box is already in view (I22)."""
  probs=[]
  for case,place in [('hidden below the keyboard',"r.top-(innerHeight-260)"),('already in view',"r.top-120")]:
    with Session(390,844) as s:
      p=s.open()
      p.evaluate(js("const r=document.querySelector('[data-guide-reply=H]').getBoundingClientRect();go(scrollY+("+place+"));"))
      settle(p,300);clear_scrolls(p)
      p.locator('[data-guide-reply=H]').focus()
      for h in (760,680,600,520,436):
        p.evaluate(KEYBOARD_ON,[390,h]);p.evaluate('window.__ss.stepAt=Math.round(performance.now()-window.__ss.t0)');settle(p,50)
      settle(p,900)
      calls=app_scrolls(p);kb=p.evaluate("document.documentElement.dataset.keyboard");step_at=p.evaluate('window.__ss.stepAt')
      if kb!='true': probs.append(f'{case}: html[data-keyboard] is {kb!r} with the 390x436 keyboard model')
      if case=='already in view' and calls: probs.append(f'{case}: the app scrolled although the box was visible: '+json.dumps(calls[:3]))
      if case!='already in view':
        if len(calls)>1: probs.append(f'{case}: the app scrolled {len(calls)} times during one keyboard opening: '+json.dumps(calls[:4]))
        elif calls:
          # the single adjustment must come after the animation settled: 400ms or more after the last keyboard step
          if calls[0]['at']<step_at+400: probs.append(f"{case}: the adjustment came {calls[0]['at']-step_at}ms after the last keyboard step; 400ms needed")
          r=p.evaluate("()=>{const t=document.querySelector('[data-guide-reply=H]').getBoundingClientRect();return [Math.round(t.top),Math.round(t.bottom)]}")
          if r[0]<0 or r[0]>436: probs.append(f'{case}: after the adjustment the box top is at {r[0]}px, outside the visible 436px')
      shot(p,'tap-'+case.replace(' ','-')+'.png');p.evaluate(KEYBOARD_OFF)
  assert not probs,' | '.join(probs)

def fab_round():
  """On phones the floating bar is one round 48x48 icon button with an accessible name and no visible word (A25)."""
  probs=[]
  for w,h in PHONES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';scroll_to(p,3*h);settle(p,300);m=bar_state(p)
      if not m['visible']: probs.append(tag+': the bar is not shown at three screens');continue
      b=m['buttons']
      if [x['fab'] for x in b]!=['contents']: probs.append(f"{tag}: expected one Contents button, got {[x['fab'] for x in b]}");continue
      c=b[0]
      if c['w']<47.5 or c['h']<47.5: probs.append(f"{tag}: the button is {c['w']:.0f}x{c['h']:.0f}; 48x48 needed")
      if abs(c['w']-c['h'])>1: probs.append(f"{tag}: the button is {c['w']:.0f}x{c['h']:.0f}, not round")
      if c['words']: probs.append(f"{tag}: the button shows the word {c['words']!r}; icon only")
      if not c['label']: probs.append(tag+': the button has no aria-label')
      shot(p,f'fab-{tag}.png')
  assert not probs,' | '.join(probs)

def fab_hidden_near_end():
  """Hidden within 48px of the end and at the very end; visible at the Save section and at three screens (A25, corrected by 2a)."""
  probs=[]
  for w,h in PHONES:
    with Session(w,h) as s:
      p=s.open();tag=f'{w}x{h}';ext=p.evaluate(js('return extent();'))
      for label,y,want in [('three screens',3*h,True),('Save section at the top',"save",True),('40px before the end',ext-40,False),('the very end',ext,False)]:
        if y=='save': y=p.evaluate(js("return document.getElementById('guide-save').getBoundingClientRect().top+scrollY-32;"))
        scroll_to(p,y);settle(p,300)
        if bar_visible(p)!=want: probs.append(f'{tag}: at {label} (scrollY {int(y)} of {ext}) the bar is {"visible" if not want else "hidden"}')
      shot(p,f'fab-end-{tag}.png')
  assert not probs,' | '.join(probs)

def fab_hidden_while_scrolling():
  """Hidden during a burst of scroll events, back within 100ms after the last one (A25)."""
  probs=[]
  with Session(390,844) as s:
    p=s.open();scroll_to(p,3*844);settle(p,300)
    if not bar_visible(p): probs.append('the bar is not shown at three screens before the burst')
    else:
      # 12 scroll events over 330ms, as a finger drag produces
      p.evaluate(js("window.__burst=new Promise(res=>{let n=0;const id=setInterval(()=>{go(scrollY+6);if(++n>=12){clearInterval(id);window.__ss.burstEnd=performance.now();res();}},30);});"))
      settle(p,180)
      if bar_visible(p): probs.append('the bar stays visible in the middle of the scroll burst')
      p.evaluate('window.__burst');settle(p,120)
      if not bar_visible(p): probs.append('the bar did not return 120ms after the last scroll event')
      shot(p,'fab-after-burst-390x844.png')
  assert not probs,' | '.join(probs)

CHECKS=[no_dynamic_units,toolbar_no_shift,tap_no_jump,fab_round,fab_hidden_near_end,fab_hidden_while_scrolling]
results=[]
def run(fn):
  name=fn.__name__
  if ONLY and name not in ONLY: return
  t=time.monotonic();status,reason='PASS',''
  try: fn()
  except AssertionError as e: status,reason='FAIL',str(e) or 'assertion failed'
  except PWTimeout as e: status,reason='ERROR','Playwright timeout: '+str(e).splitlines()[0]
  except Exception as e: status,reason='ERROR',f'{type(e).__name__}: '+(str(e).splitlines()[0] if str(e) else '')
  line=' '.join(reason.split());print(f'{status} {name}'+(f' - {line[:700]}' if line else ''),flush=True)
  results.append({'check':name,'result':status,'reason':reason,'seconds':round(time.monotonic()-t,1)})

unknown=ONLY-{f.__name__ for f in CHECKS}
if unknown: sys.exit('unknown check(s) in SCROLL_CHECKS: '+', '.join(sorted(unknown)))
fresh_build()
server=QuietServer(('127.0.0.1',0),VercelHeaders);threading.Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_address[1]}/'
try:
  with sync_playwright() as pw:
    kwargs={'args':['--no-sandbox']} if ENGINE=='chromium' else {}
    if ENGINE=='chromium' and os.environ.get('CHROMIUM_PATH'): kwargs['executable_path']=os.environ['CHROMIUM_PATH']
    browser=getattr(pw,ENGINE).launch(**kwargs)
    for fn in CHECKS: run(fn)
    browser.close()
finally:
  server.shutdown()
  (OUT/f'scroll-stability-{ENGINE}-results.json').write_text(json.dumps({'engine':ENGINE,'keyboard':'visualViewport geometry model, not a device keyboard','toolbar':'viewport-height steps, not Safari','results':results},indent=1))
failed=[r for r in results if r['result'] in ('FAIL','ERROR')]
print(f"{sum(r['result']=='PASS' for r in results)} passed, {len(failed)} failed",flush=True)
sys.exit(1 if failed or not results else 0)
