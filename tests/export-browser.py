"""Save/download UI tests. DOM mode explicitly simulates storage and tab handoff.
Run: BROWSER_MODE=dom python tests/export-browser.py
Default HTTP mode tests real same-origin tabs when navigation is allowed.
"""
import functools, json, os, re, threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('EVIDENCE_DIR',str(ROOT.parent/'export-evidence')))
OUT.mkdir(parents=True,exist_ok=True)
MODE=os.environ.get('BROWSER_MODE','http')
CONFIG=json.loads((ROOT/'vercel.json').read_text())
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*_): pass
    def end_headers(self):
        for h in CONFIG['headers'][0]['headers']: self.send_header(h['key'],h['value'])
        super().end_headers()
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'public')))
threading.Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_port}/'
RESULTS=[]
def check(name,condition):
    assert condition,name
    RESULTS.append({'test':name,'status':'Passed'})
    print('PASS',name,flush=True)
def boot(ctx,seed=None,fragment='',open_mode='mock'):
    p=ctx.new_page();p.set_default_timeout(5000)
    if MODE=='dom':
        s=(ROOT/'index.html').read_text()
        s=re.sub(r'<script\b[^>]*>.*?</script>','',s,flags=re.S)
        s=re.sub(r'<link\b[^>]*>','',s)
        p.set_content(s);p.add_style_tag(content=(ROOT/'styles.css').read_text());p.add_style_tag(content=(ROOT/'export-view.css').read_text())
        p.evaluate('''seed=>{const data={...seed};Object.defineProperty(window,'localStorage',{value:{
        getItem:k=>data[k]??null,setItem:(k,v)=>{data[k]=String(v)},snapshot:()=>({...data})}})}''',seed or {})
        if fragment:p.evaluate("x=>history.replaceState(null,'','#'+x)",fragment)
        for asset in ['core.js','export.js','app.js']:p.add_script_tag(content=(ROOT/asset).read_text())
    else:
        p.goto(URL)
        if seed:p.evaluate('(s)=>Object.entries(s).forEach(([k,v])=>localStorage.setItem(k,v))',seed)
        if seed or fragment:p.goto(URL+'#'+fragment);p.reload()
    if open_mode=='mock':
        p.evaluate('''()=>{window.OPENED=[];window.open=(url,target)=>{const t={opener:'initial',location:{replace:u=>{t.url=u}}};
        OPENED.push({tab:t,initial:url,target,saved:JSON.parse(localStorage.getItem('wholehearted-journal-v2'))});return t;};}''')
    elif open_mode=='blocked':p.evaluate('window.open=()=>null')
    return p

def prepare(p):
    p.locator('[data-action=new]').first.click()
    p.locator('[data-field=topic]').fill('Responding to a difficult conversation')
    p.locator('[data-step="3"]').first.click()
    for key,kind,note in [('W','thank','willingness to listen'),('E','thank','strength to pause'),('E','ask','gentleness while still hurt')]:
        p.locator(f'[data-area="{key}"]').click()
        p.locator(f'[data-field="areas.{key}.{kind}"]').check()
        p.locator(f'[data-field="areas.{key}.{kind}Note"]').fill(note)
    p.locator('[data-step="4"]').first.click()
    p.locator('[data-field=prayer]').fill('Father, thank you for helping me pause.\nPlease help me respond gently. Amen.')
    p.locator('[data-step="5"]').first.click()
    p.locator('[data-field=nextStep]').fill('Listen first and speak privately.')

with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
    p=boot(ctx,open_mode='mock' if MODE=='dom' else 'native');prepare(p)
    if MODE=='dom':
        p.locator('[data-action=save]').click()
        opened=p.evaluate('OPENED')
        check('Save verifies persistence before requesting a new tab',len(opened)==1 and len(opened[0]['saved']['entries'])==1)
        check('New tab has no opener and its URL contains only the local record ID',opened[0]['tab']['opener'] is None and '#download-p-' in opened[0]['tab']['url'] and 'conversation' not in opened[0]['tab']['url'])
        d=opened[0]['saved']['entries'][0]
        child=boot(ctx,p.evaluate('localStorage.snapshot()'),'download-'+d['id'])
    else:
        with ctx.expect_page() as popup:p.locator('[data-action=save]').click()
        child=popup.value;child.wait_for_selector('[data-action=download-html]')
        check('Save opens a real same-origin download tab',child.url.startswith(URL+'#download-'))
        check('New tab has no opener',child.evaluate('window.opener===null'))
        d=child.evaluate('JSON.parse(localStorage.getItem("wholehearted-journal-v2")).entries[0]')
    check('Download page identifies where the entry and file live','Saved in this browser' in child.locator('main').text_content() and 'separate, readable file' in child.locator('main').inner_text())
    check('Download preview preserves the edited prayer and mixed notes',d['prayer'] in child.locator('.export-sheet').inner_text() and 'strength to pause' in child.locator('.export-sheet').inner_text() and 'gentleness while still hurt' in child.locator('.export-sheet').inner_text())
    with child.expect_download() as info:child.locator('[data-action=download-html]').click()
    download=info.value;content=Path(download.path()).read_text()
    check('Download produces an actual standalone HTML file',download.suggested_filename.endswith('.html') and content.startswith('<!doctype html>'))
    check('The HTML copy retains edited prayer, next step and source links',d['prayer'] in content and d['nextStep'] in content and all(x in content for x in ['www.esv.org','www.stepbible.org','www.blueletterbible.org','app.logos.com']))
    (OUT/'Wholehearted-sample-prayer.html').write_text(content)
    child.screenshot(path=str(OUT/'download-mobile.png'),full_page=True)
    offline=ctx.new_page();requests=[];offline.on('request',lambda r:requests.append(r.url));offline.set_content(content)
    check('Downloaded HTML renders independently with no scripts or automatic requests',offline.locator('h1').count()==1 and offline.locator('script').count()==0 and not requests)
    for w in [320,390,768,1440]:
        child.set_viewport_size({'width':w,'height':900});offline.set_viewport_size({'width':w,'height':900})
        check(f'Download page and standalone file fit {w}px',child.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and offline.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    offline.screenshot(path=str(OUT/'html-desktop.png'),full_page=True)
    offline.emulate_media(media='print')
    check('HTML remains readable in print media',offline.locator('.export-sheet').is_visible() and offline.locator('h1').is_visible())
    ctx.close()
    ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
    p=boot(ctx,open_mode='blocked');prepare(p);p.locator('[data-action=save]').click()
    check('Blocked popup keeps the saved entry and offers an inline HTML download','new tab was blocked' in p.locator('#notice').inner_text() and p.locator('[data-action=download-html]').is_visible())
    with p.expect_download() as info:p.locator('[data-action=download-html]').click()
    check('Popup-blocked fallback still downloads HTML',info.value.suggested_filename.endswith('.html'))
    p=boot(ctx,fragment='download-missing')
    check('Missing record gives an honest non-shareable-link explanation','Prayer not available here' in p.locator('main').inner_text() and p.locator('[data-action=download-html]').count()==0)
    ctx.close()
    ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
    p=boot(ctx);prepare(p)
    target='localStorage' if MODE=='dom' else 'Storage.prototype'
    p.evaluate("()=>{"+target+".setItem=()=>{throw Error('Full')}}")
    p.locator('[data-action=save]').click()
    check('Storage failure does not open a falsely saved prayer','Not saved' in p.locator('#notice').inner_text() and len(p.evaluate('OPENED'))==0)
    with p.expect_download() as info:p.locator('[data-action=download-html]').click()
    check('Storage failure still allows a personal HTML copy',info.value.suggested_filename.endswith('.html'))
    ctx.close();b.close()
server.shutdown()
(OUT/'tests.json').write_text(json.dumps({'mode':MODE,'tests':RESULTS},indent=2))
print(f'{len(RESULTS)} tests passed. Mode={MODE}; DOM mode is not a native navigation/storage test.',flush=True)
