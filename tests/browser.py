"""Run against the local static build. Requires Playwright and Chromium only for tests."""
import functools
import json
import os
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path(os.environ.get('EVIDENCE_DIR', str(ROOT.parent / 'evidence')))
EVIDENCE.mkdir(parents=True, exist_ok=True)
CONFIG = json.loads((ROOT / 'vercel.json').read_text())

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def end_headers(self):
        for header in CONFIG['headers'][0]['headers']:
            self.send_header(header['key'], header['value'])
        super().end_headers()

server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT / 'public')))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{server.server_port}/'
RESULTS = []
errors = []
requests = []
MODE = os.environ.get('BROWSER_MODE','http')

def boot(ctx, seed=None, init=None, fragment=''):
    page=ctx.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: requests.append(r.url))
    if MODE == 'dom':
        html=(ROOT/'public/index.html').read_text()
        html=re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S)
        html=re.sub(r'<link\b[^>]*>', '', html)
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'public/styles.css').read_text())
        page.evaluate("""seed=>{
            const data={...seed};
            Object.defineProperty(window,'localStorage',{configurable:true,value:{
                getItem:k=>Object.prototype.hasOwnProperty.call(data,k)?data[k]:null,
                setItem:(k,v)=>{data[k]=String(v)},
                snapshot:()=>({...data})
            }});
        }""", seed or {})
        if init:page.evaluate(init)
        if fragment:page.evaluate("hash=>history.replaceState(null,'','#'+hash)",fragment)
        page.add_script_tag(content=(ROOT/'public/core.js').read_text())
        page.add_script_tag(content=(ROOT/'public/app.js').read_text())
    else:
        if init:page.add_init_script(init)
        page.goto(URL)
        if seed:
            page.evaluate('(s)=>Object.entries(s).forEach(([k,v])=>localStorage.setItem(k,v))',seed)
            page.reload()
        if fragment:page.goto(URL+'#'+fragment)
    return page


def check(name, fn):
    try:
        fn()
        RESULTS.append({'test':name,'status':'Passed'})
        print('PASS', name, flush=True)
    except Exception as exc:
        RESULTS.append({'test':name,'status':'Failed','detail':str(exc)})
        print('FAIL', name, str(exc), flush=True)
        raise

def click(p, action):
    p.locator(f'[data-action="{action}"]').first.click()

def begin(p, topic='How should I respond?', thanks=False):
    click(p, 'thanks' if thanks else 'new')
    p.locator('[data-field="topic"]').fill(topic)
    click(p,'next')

def reach_prayer(p):
    begin(p)
    click(p,'next')
    p.locator('[data-step="4"]').first.click()

def area_note(p, key, kind, note):
    p.locator(f'[data-area="{key}"]').click()
    p.locator(f'[data-field="areas.{key}.{kind}"]').check()
    p.locator(f'[data-field="areas.{key}.{kind}Note"]').fill(note)

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
    p = boot(context)
    p.wait_for_selector('h1')
    def home():
        assert p.title() == 'Wholehearted · W.H.E.M.S. Prayer'
        assert p.locator('h1').count()==1
        assert p.locator('[data-action="thanks"]').count()==1
        p.screenshot(path=str(EVIDENCE/'home-desktop.png'),full_page=True)
    check('Home and no-login thanksgiving entry',home)
    def validation():
        click(p,'new')
        click(p,'next')
        assert 'Please name' in p.locator('#notice').inner_text()
        assert p.locator('[data-field="topic"]').evaluate('(el)=>el===document.activeElement')
    check('Required matter validation and focus',validation)
    def mixed():
        p.locator('[data-field="topic"]').fill('Respond to unfair criticism')
        click(p,'next')
        p.locator('[data-field="gate"][value="principles"]').check()
        p.locator('[data-field="scripture"]').fill('James 1:19 - listen before speaking.')
        click(p,'next')
        for key,note in [('W','being willing to listen'),('M','clearer understanding'),('S','the gospel I am learning')]:
            area_note(p,key,'thank',note)
        area_note(p,'H','ask','correct my wish to embarrass them')
        area_note(p,'E','ask','answer gently while still hurt')
        p.set_viewport_size({'width':430,'height':932})
        p.screenshot(path=str(EVIDENCE/'reflection-mobile.png'),full_page=True)
        p.locator('[data-step="4"]').first.click()
        value=p.locator('[data-field="prayer"]').input_value()
        for phrase in ['being willing to listen','clearer understanding','the gospel I am learning','correct my wish','still hurt']:
            assert phrase in value
        assert 'someone who belongs to him' not in value
        assert '60%' not in value
    check('Three thanks plus two requests and no assumed salvation',mixed)
    def both():
        p.locator('[data-step="3"]').first.click()
        area_note(p,'E','thank','the strength to pause')
        assert p.locator('[data-field="areas.E.ask"]').is_checked()
        p.locator('[data-step="4"]').first.click()
        p.once('dialog',lambda d:d.accept())
        click(p,'regenerate')
        value=p.locator('[data-field="prayer"]').input_value()
        assert 'the strength to pause' in value and 'still hurt' in value
    check('Both invitations can coexist in the same area',both)
    def fruit_edits():
        p.locator('.fruit-panel summary').click()
        p.locator('[data-fruit="Gentleness"]').check()
        p.once('dialog',lambda d:d.accept())
        click(p,'regenerate')
        assert 'gentleness' in p.locator('[data-field="prayer"]').input_value()
        p.locator('[data-field="prayer"]').fill('Father, help me listen and speak with love. Amen.')
        p.locator('[data-step="3"]').first.click()
        p.locator('[data-step="4"]').first.click()
        assert p.locator('[data-field="prayer"]').input_value()=='Father, help me listen and speak with love. Amen.'
        p.screenshot(path=str(EVIDENCE/'prayer-mobile.png'),full_page=True)
    check('Optional fruit and retained user edits',fruit_edits)
    def save():
        global p
        click(p,'next')
        p.locator('[data-field="nextStep"]').fill('Listen first, then speak privately.')
        click(p,'save')
        assert 'Saved in this browser' in p.locator('#notice').inner_text()
        data=p.evaluate('JSON.parse(localStorage.getItem("wholehearted-journal-v2"))')
        assert len(data['entries'])==1
        assert data['entries'][0]['prayer']=='Father, help me listen and speak with love. Amen.'
        if MODE=='dom':
            snapshot=p.evaluate('localStorage.snapshot()')
            fragment=p.url.split('#')[-1]
            p.close()
            p=boot(context,seed=snapshot,fragment=fragment)
        else:
            p.reload()
        assert 'Father, help me listen' in p.locator('.read-prayer').inner_text()
    check('Save, reload and read edited prayer',save)
    def review():
        original=p.evaluate('localStorage.getItem("wholehearted-journal-v2")')
        original_id=json.loads(original)['entries'][0]['id']
        click(p,'review')
        assert p.locator('[data-field="topic"]').input_value()=='Respond to unfair criticism'
        click(p,'next');click(p,'next')
        area_note(p,'H','thank','a gentler motive')
        area_note(p,'E','thank','restraint even while hurt')
        p.locator('[data-step="4"]').first.click()
        value=p.locator('[data-field="prayer"]').input_value()
        assert 'a gentler motive' in value and 'restraint even while hurt' in value
        assert 'clearer understanding' not in value
        click(p,'next');click(p,'save')
        entries=p.evaluate('JSON.parse(localStorage.getItem("wholehearted-journal-v2")).entries')
        assert len(entries)==2
        assert entries[0]['parentId']==original_id
        assert entries[1]==json.loads(original)['entries'][0]
    check('Return with thanks for two areas; preserve original snapshot',review)
    def export():
        with p.expect_download() as info:
            click(p,'download')
        out=info.value.path()
        assert 'a gentler motive' in Path(out).read_text()
        assert not any(not u.startswith(URL) for u in requests)
    check('Text export and zero third-party runtime requests',export)
    def keyboard():
        p.locator('[data-route="home"]').first.click()
        p.keyboard.press('Control+Home')
        p.locator('.skip').focus()
        p.keyboard.press('Enter')
        assert p.locator('#main').evaluate('(el)=>el===document.activeElement')
        click(p,'new')
        p.locator('[data-field="topic"]').fill('Keyboard prayer')
        click(p,'next');click(p,'next')
        cb=p.locator('[data-field="areas.W.thank"]')
        cb.focus();p.keyboard.press('Space')
        assert cb.is_checked()
        assert p.locator('[data-field="areas.W.thankNote"]').is_visible()
        missing=p.locator('input,textarea,select').evaluate_all('(els)=>els.filter(e=>!e.labels?.length && !e.getAttribute("aria-label")).length')
        assert missing==0
    check('Keyboard focus, skip link and labelled native controls',keyboard)
    def responsive():
        for width in [320,390,430,768,1024,1440]:
            p.set_viewport_size({'width':width,'height':900})
            for step in [1,2,3,4,5]:
                p.locator(f'[data-step="{step}"]').first.click()
                assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,step)
        p.set_viewport_size({'width':390,'height':844})
        p.locator('[data-route="home"]').first.click()
        p.screenshot(path=str(EVIDENCE/'home-mobile.png'),full_page=True)
        assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    check('Five steps at six viewport widths without horizontal overflow',responsive)
    assert not errors, errors
    context.close()

    def isolated(fn, seed=None, init=None):
        ctx=browser.new_context(viewport={'width':390,'height':844},accept_downloads=True)
        page=boot(ctx,seed=seed,init=init)
        try:fn(page)
        finally:ctx.close()

    def fresh_thanks(p):
        begin(p,'A friend’s practical help',True)
        click(p,'next');area_note(p,'H','thank','the kindness shown to me')
        p.locator('[data-step="4"]').first.click()
        assert 'I return to you' in p.locator('[data-field="prayer"]').input_value()
    check('Fresh thanksgiving without an earlier saved prayer',lambda:isolated(fresh_thanks))

    def xss(p):
        attack='</textarea><img src=x onerror="window.PWNED=1"><script>window.PWNED=1</script>'
        begin(p,attack);click(p,'next');area_note(p,'H','ask',attack)
        p.locator('[data-step="4"]').first.click();click(p,'next');click(p,'save')
        assert attack in p.locator('.read-prayer').inner_text()
        assert p.evaluate('window.PWNED') is None
        assert p.locator('#main img').count()==0
    check('Reflections rendered as text, including script-like input',lambda:isolated(xss))

    def blocked(p):
        reach_prayer(p);click(p,'next');click(p,'save')
        assert 'could not be read' in p.locator('#notice').inner_text()
        assert 'flow-5' in p.url
    check('Blocked browser storage keeps prayer usable and reports failure',lambda:isolated(blocked,init="Object.defineProperty(window,'localStorage',{get(){throw new Error('Blocked')}})"))

    def quota(p):
        reach_prayer(p)
        target="localStorage" if MODE=="dom" else "Storage.prototype"
        p.evaluate("()=>{"+target+".setItem=function(){throw new DOMException('Full','QuotaExceededError')};}")
        click(p,'next');click(p,'save')
        assert 'Not saved' in p.locator('#notice').inner_text()
        assert 'flow-5' in p.url
    check('Quota failure never claims a successful save',lambda:isolated(quota))

    def corrupt(p):
        p.locator('[data-route="journal"]').click()
        click(p,'backup')
        assert 'Use Download existing raw data' in p.locator('#notice').inner_text()
        assert p.evaluate('localStorage.getItem("wholehearted-journal-v2")')=='{bad-json'
        with p.expect_download() as info:click(p,'raw-backup')
        assert Path(info.value.path()).read_text()=='{bad-json'
    check('Corrupt data preserved and exportable without empty backup',lambda:isolated(corrupt,seed={'wholehearted-journal-v2':'{bad-json'}))

    legacy=json.dumps({'decision':'Earlier decision','scriptureStatus':'clear','whems':{'S':{'status':'aligned','note':'Grace'},'H':{'status':'struggling','note':'Motive'}},'review':{'note':'Earlier thanks'}})
    def migration(p):
        p.locator('[data-route="journal"]').click();click(p,'migrate')
        entries=p.evaluate('JSON.parse(localStorage.getItem("wholehearted-journal-v2")).entries')
        assert entries[0]['belonging']==''
        assert entries[0]['legacyNote']=='Earlier thanks'
        assert p.evaluate('localStorage.getItem("wholehearted-prayer-v1")')==legacy
    check('Explicit v1 migration preserves old storage and review note',lambda:isolated(migration,seed={'wholehearted-prayer-v1':legacy}))

    def deletion(p):
        reach_prayer(p);click(p,'next');click(p,'save')
        p.once('dialog',lambda d:d.dismiss());click(p,'delete')
        assert len(p.evaluate('JSON.parse(localStorage.getItem("wholehearted-journal-v2")).entries'))==1
        p.once('dialog',lambda d:d.accept());click(p,'delete')
        assert len(p.evaluate('JSON.parse(localStorage.getItem("wholehearted-journal-v2")).entries'))==0
    check('Deletion requires confirmation and can be cancelled',lambda:isolated(deletion))

    def copy_failure(p):
        reach_prayer(p)
        p.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(Error('Denied'))}})")
        click(p,'copy')
        p.wait_for_function("document.getElementById('notice').textContent.includes('Automatic copy is unavailable')")
        assert p.locator('[data-field="prayer"]').evaluate('(e)=>e.selectionEnd>e.selectionStart')
    check('Clipboard denial offers manual copy, not false success',lambda:isolated(copy_failure))
    assert not errors, errors
    browser.close()
server.shutdown()
(EVIDENCE/'browser-tests.json').write_text(json.dumps(RESULTS,indent=2))
print(f'{len(RESULTS)} browser scenarios passed. Mode={MODE}. DOM mode injects assets and uses a storage fixture; not a network end-to-end or native Safari test.')
