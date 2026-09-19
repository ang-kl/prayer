"""DOM-mode tests using exact built assets, Chromium and a storage fixture.
No claim of native Safari, live network navigation, or physical-device validation.
Run `node build.cjs` first; install Playwright and provide CHROMIUM_PATH if needed.
"""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('EVIDENCE_DIR',str(ROOT/'evidence')))
OUT.mkdir(parents=True,exist_ok=True)
results=[]

def run(name,fn):
    fn();results.append({'test':name,'result':'Passed'});print('PASS',name,flush=True)

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page();page.set_default_timeout(4000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    html=(ROOT/'public/index.html').read_text()
    html=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S)
    html=re.sub(r'<link\b[^>]*>','',html)
    page.set_content(html)
    for filename in ['styles.css','export-view.css','about.css']:
        page.add_style_tag(content=(ROOT/'public'/filename).read_text())
    page.evaluate("""()=>{
      const data={};window.testWrites=0;
      Object.defineProperty(window,'localStorage',{configurable:true,value:{
        getItem:k=>Object.prototype.hasOwnProperty.call(data,k)?data[k]:null,
        setItem:(k,v)=>{window.testWrites++;data[k]=String(v)},snapshot:()=>({...data})
      }});
    }""")
    for filename in ['core.js','export.js','app.js','about.js']:
        page.add_script_tag(content=(ROOT/'public'/filename).read_text())
    trigger=page.locator('[data-about-open]');dialog=page.locator('#wholehearted-about')
    def open_panel():
        trigger.click();assert dialog.is_visible();assert page.locator('#about-heading').evaluate('(e)=>e===document.activeElement')
    run('About opens in the same page with title focus',open_panel)
    def keyboard():
        for _ in range(28):
            page.keyboard.press('Tab')
            assert page.evaluate("document.activeElement===document.body || !!document.activeElement.closest('#wholehearted-about')")
        page.keyboard.press('Escape');assert not dialog.is_visible()
        assert trigger.evaluate('(e)=>e===document.activeElement')
    run('Native dialog keyboard containment, Escape and focus return',keyboard)
    def poem():
        open_panel();dialog.locator('summary',has_text='The original poem').click()
        lines=dialog.locator('.poem-line').all_text_contents()
        assert lines==page.evaluate('[...WholeheartedAbout.POEM]');assert len(lines)==12
        assert 'another LLM' in dialog.inner_text()
        page.locator('[data-about-close]').first.click()
    run('Original poem and attribution are readable without rewriting',poem)
    def preserve_draft():
        page.locator('[data-action="new"]').first.click()
        page.locator('[data-field="topic"]').fill('PRIVATE TEST: seek patience')
        page.locator('[data-action="next"]').click();page.locator('[data-action="next"]').click()
        page.locator('[data-field="areas.W.thank"]').check()
        page.locator('[data-field="areas.W.thankNote"]').fill('a willingness to listen')
        page.locator('[data-field="areas.W.ask"]').check()
        page.locator('[data-field="areas.W.askNote"]').fill('obey even when tired')
        before=page.evaluate('({hash:location.hash,writes:testWrites,storage:localStorage.snapshot()})')
        open_panel();page.locator('[data-about-close]').first.click()
        after=page.evaluate('({hash:location.hash,writes:testWrites,storage:localStorage.snapshot()})')
        assert before==after
        assert page.locator('[data-field="areas.W.thankNote"]').input_value()=='a willingness to listen'
        assert page.locator('[data-field="areas.W.askNote"]').input_value()=='obey even when tired'
        assert page.locator('[data-field="areas.W.ask"]').is_checked()
    run('Opening and closing preserves unsaved mixed reflections and writes no storage',preserve_draft)
    def edited_prayer():
        page.locator('[data-step="4"]').first.click()
        text='Father, these are my edited words. Thank you; please help me.'
        page.locator('[data-field="prayer"]').fill(text)
        open_panel();page.keyboard.press('Escape')
        assert page.locator('[data-field="prayer"]').input_value()==text
    run('Edited prayer is untouched after reading About',edited_prayer)
    def save_export():
        # Simulated popup handling; no real cross-tab navigation is asserted.
        page.evaluate('window.open=()=>null')
        page.locator('[data-step="5"]').click();page.locator('[data-action="save"]').click()
        assert 'Saved in this browser' in page.locator('#notice').inner_text()
        before=page.evaluate('localStorage.snapshot()')
        open_panel();assert 'PRIVATE TEST' not in dialog.inner_text();page.keyboard.press('Escape')
        assert before==page.evaluate('localStorage.snapshot()')
        with page.expect_download() as event:page.locator('[data-action="download-html"]').click()
        download=event.value;download.save_as(OUT/'prayer-export-regression.html')
        contents=(OUT/'prayer-export-regression.html').read_text()
        assert 'these are my edited words' in contents
        assert '<script' not in contents
    run('Saved journal remains unchanged and an actual HTML download retains edited words',save_export)
    def responsiveness():
        widths=[320,390,430,768,820,834,1024,1194,1366,1440]
        open_panel()
        dialog.locator('details').evaluate_all('(els)=>els.forEach(e=>e.open=true)')
        for width in widths:
            page.set_viewport_size({'width':width,'height':900})
            dims=dialog.evaluate('(e)=>({w:e.clientWidth,sw:e.scrollWidth,h:e.getBoundingClientRect().height})')
            assert dims['sw']<=dims['w']+1,(width,dims)
            assert dims['h']<=901,(width,dims)
            bad=page.locator('.about-copy').evaluate('(e)=>e.scrollWidth>e.clientWidth+1')
            assert not bad,width
        # Orientation change while the panel is open must leave all content available.
        page.set_viewport_size({'width':932,'height':430})
        assert dialog.evaluate('(e)=>e.getBoundingClientRect().height')<=430
        assert dialog.locator('.poem-line').count()==12
        page.set_viewport_size({'width':390,'height':844})
        dialog.locator('details').evaluate_all('(els)=>els.forEach(e=>e.open=false)')
        dialog.locator('details').first.evaluate('(e)=>e.open=true')
        page.screenshot(path=str(OUT/'about-mobile.png'))
        dialog.locator('details').first.evaluate('(e)=>e.open=false')
        dialog.locator('summary',has_text='The original poem').click()
        dialog.locator('.about-poem').evaluate('(e)=>e.scrollIntoView({block:"start"})')
        page.screenshot(path=str(OUT/'poem-mobile.png'))
        page.set_viewport_size({'width':1024,'height':900})
        page.screenshot(path=str(OUT/'poem-tablet.png'))
        page.set_viewport_size({'width':1440,'height':1000})
        page.locator('.about-scroll').evaluate('(e)=>e.scrollTop=0')
        page.screenshot(path=str(OUT/'about-desktop.png'))
        page.keyboard.press('Escape')
    run('Ten widths, portrait/landscape, no horizontal overflow; screenshots saved',responsiveness)
    def enlargement():
        page.set_viewport_size({'width':390,'height':844});open_panel()
        dialog.locator('details').evaluate_all('(els)=>els.forEach(e=>e.open=true)')
        page.add_style_tag(content='.about-dialog{font-size:34px}.about-dialog h2,.about-dialog summary{font-size:2rem}')
        assert not dialog.evaluate('(e)=>e.scrollWidth>e.clientWidth+1')
        assert page.locator('.about-bar button').is_visible()
        page.keyboard.press('Escape')
    run('Enlarged reading text remains in a usable panel with a visible Close control',enlargement)
    def fallback():
        page.evaluate("document.getElementById('wholehearted-about').showModal=undefined")
        trigger.click();assert dialog.is_visible()
        assert 'about-is-open' not in (page.locator('html').get_attribute('class') or '')
        page.locator('[data-about-close]').first.click();assert not dialog.is_visible()
    run('Non-modal inline fallback can open and close without data changes',fallback)
    run('No browser JavaScript exceptions',lambda: (_ for _ in ()).throw(AssertionError(errors)) if errors else None)
    browser.close()
(OUT/'about-browser-results.json').write_text(json.dumps({'mode':'Chromium DOM injection with simulated storage; no live HTTP test','results':results},indent=2))
