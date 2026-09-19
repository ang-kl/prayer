"""Exact built assets in Chromium DOM mode with explicit storage and ESV-response fixtures.
No live HTTP navigation, real cross-tab localStorage or native Apple-device claim.
Run node build.cjs first. Requires Python Playwright and Chromium.
"""
import os,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('EVIDENCE_DIR',str(ROOT/'evidence')))
OUT.mkdir(parents=True,exist_ok=True)
results=[]

def check(name,fn):
    fn();results.append({'test':name,'result':'Passed'});print('PASS',name,flush=True)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    ctx=browser.new_context(viewport={'width':1440,'height':1100},accept_downloads=True)
    page=ctx.new_page();page.set_default_timeout(4000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def boot(seed=''):
        page.once('dialog',lambda d:d.accept()) if False else None
        page.set_content('<!doctype html><html><body></body></html>')
        page.evaluate("history.replaceState(null,'','#pray')")
        html=(ROOT/'public/index.html').read_text()
        html=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S)
        html=re.sub(r'<link\b[^>]*>','',html)
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'public/styles.css').read_text())
        page.evaluate("""()=>{
          const data={};window.testWrites=0;window.popupCalls=0;window.lastPopup='';window.apiCalls=[];window.sourceEnabled=false;window.failStorage=false;
          Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.hasOwn(data,k)?data[k]:null,setItem:(k,v)=>{if(window.failStorage)throw Error('quota');window.testWrites++;data[k]=String(v)},snapshot:()=>({...data})}});
          window.open=()=>{window.popupCalls++;return {opener:window,location:{replace:u=>window.lastPopup=u},close:()=>{}}};
          window.fetch=async(url,options)=>{
            window.apiCalls.push(String(url));const id=new URL(url,'https://test.invalid').searchParams.get('id');
            if(!window.sourceEnabled)return {ok:false,json:async()=>({code:'SOURCE_NOT_CONFIGURED',error:'The ESV text connection is not enabled yet. The passage notes are available, but they are not the Bible text.'})};
            return {ok:true,json:async()=>({id,translation:'ESV',text:'PROVIDER FIXTURE - not Scripture. <img src=x onerror=alert(1)>'})};
          };
        }""")
        for file in ['build-info.js','theme.js','core.js','journal.js','catalogue.js','export.js','about.js']:
            page.add_script_tag(content=(ROOT/'public'/file).read_text())
        if seed:page.evaluate(seed)
        page.evaluate('window.testWrites=0')
        page.add_script_tag(content=(ROOT/'public/app.js').read_text())
    page.on('dialog',lambda d:d.accept())
    seed="""()=>{const C=WholeheartedCore;let d=C.blank('seek','2026-09-18T02:00:00Z','original');d.topic='PRIVATE OLD REQUEST';d.prayer='PRIVATE OLD PRAYER TEXT';localStorage.setItem(C.STORAGE,JSON.stringify({version:2,entries:[d]}));window.originalV2=localStorage.getItem(C.STORAGE);}"""
    boot(seed)
    def initial():
        assert page.get_by_text('Build 0.0.001',exact=True).is_visible()
        assert '2.1' not in page.locator('body').inner_text()
        assert 'PRIVATE OLD REQUEST' not in page.locator('body').inner_text()
        page.locator('nav [data-route=journal]').click()
        assert 'PRIVATE OLD REQUEST' not in page.locator('body').inner_text()
        assert page.locator('[data-field=prayer]').input_value()==''
    check('Fresh Pray and Journal do not display earlier titles or prayers',initial)
    def deliberate_browse():
        page.locator('[data-action=browse]').click()
        assert page.get_by_role('button',name='PRIVATE OLD REQUEST',exact=True).is_visible()
        assert 'PRIVATE OLD PRAYER TEXT' not in page.locator('body').inner_text()
        page.locator('nav [data-route=journal]').click()
        assert 'PRIVATE OLD REQUEST' not in page.locator('body').inner_text()
    check('Only Browse exposes the title; never a private excerpt',deliberate_browse)
    def write_and_type():
        page.locator('details[data-details=record] summary').click()
        page.locator('[data-field=topic]').fill('Patience in a conversation')
        page.locator('[data-field=prayer]').fill('Father, thank you for clarity; please help me respond gently.')
        page.locator('[data-field=entryType][value=mixed]').check()
        page.locator('[data-field=form]').select_option('personal')
        page.locator('details[data-area=H] summary').click()
        page.locator('[data-field="areas.H.thank"]').check()
        page.locator('[data-field="areas.H.ask"]').check()
        page.locator('[data-field="areas.H.thankNote"]').fill('the care you are growing in me')
        page.locator('[data-field="areas.H.askNote"]').fill('honest motives')
        assert page.evaluate('testWrites')==0
    check('Mixed type and both invitations work without automatic saving',write_and_type)
    def modal():
        page.locator('[data-verse=philippians-4-6-7]').first.click()
        assert page.locator('#reader').is_visible()
        assert page.locator('#reader-heading').evaluate('(e)=>e===document.activeElement')
        page.wait_for_function("document.getElementById('passage-state').innerText.includes('unavailable')")
        assert 'not the Bible text' in page.locator('#passage-state').inner_text()
        assert page.evaluate('popupCalls')==0
        page.screenshot(path=str(OUT/'verse-reader-mobile-unconfigured.png'))
        page.keyboard.press('Escape')
        assert not page.locator('#reader').is_visible()
        assert page.locator('[data-field=prayer]').input_value().startswith('Father, thank you')
        assert page.locator('[data-field="areas.H.askNote"]').input_value()=='honest motives'
        assert page.evaluate('testWrites')==0
    check('Verse reader stays in-page, labels missing text and preserves unsaved writing',modal)
    def focus_back():
        trigger=page.locator('[data-verse=philippians-4-6-7]').first
        trigger.click()
        for _ in range(18):
            page.keyboard.press('Tab')
            assert page.evaluate("document.activeElement===document.body||!!document.activeElement.closest('#reader')")
        page.locator('#reader [data-verse=james-1-5]').click()
        assert 'James 1:5' in page.locator('#reader-heading').inner_text()
        page.locator('[data-action=reader-back]').click()
        assert 'Philippians 4:6-7' in page.locator('#reader-heading').inner_text()
        page.keyboard.press('Escape');assert trigger.evaluate('(e)=>e===document.activeElement')
    check('Keyboard focus, cross-reference Back and return focus work',focus_back)
    def fixture_safety():
        page.evaluate('sourceEnabled=true')
        page.locator('[data-verse=philippians-4-6-7]').first.click()
        page.wait_for_selector('.scripture-text')
        assert 'PROVIDER FIXTURE' in page.locator('.scripture-text').inner_text()
        assert page.locator('.scripture-text img').count()==0
        page.locator('[data-action=attach-ref]').click()
        page.keyboard.press('Escape')
        for call in page.evaluate('apiCalls'):
            assert call.startswith('/api/scripture?id=')
            assert not any(s in call for s in ['Father','Patience','motives','PRIVATE'])
    check('Only public IDs are requested; provider content is rendered as text',fixture_safety)
    def save():
        page.locator('[data-action=save]').click()
        assert 'Saved on this device' in page.locator('#notice').inner_text()
        assert page.evaluate('popupCalls')==1
        assert page.evaluate('lastPopup').split('#')[-1].startswith('download-p-')
        assert 'Patience' not in page.evaluate('lastPopup')
        assert page.locator('[data-field=prayer]').input_value()==''
        assert page.evaluate('localStorage.getItem(WholeheartedCore.STORAGE)===originalV2')
        assert page.evaluate('JSON.parse(localStorage.getItem(WholeheartedJournal.STORAGE)).entries.length')==2
    check('Save verifies storage, retains v2 data and requests only the download tab',save)
    def export_file():
        with page.expect_download() as ev:page.locator('#notice [data-action=download-html]').click()
        f=ev.value;f.save_as(OUT/'prayer-reading-copy.html');s=(OUT/'prayer-reading-copy.html').read_text()
        for part in ['Father, thank you for clarity','Mixed','honest motives','0.0.001']:assert part in s
        assert '<script' not in s
        assert 'PROVIDER FIXTURE' not in s
    check('Actual standalone HTML download keeps writing, metadata and build identity',export_file)
    def journal_hide():
        page.locator('nav [data-route=journal]').click()
        assert 'Patience in a conversation' not in page.locator('body').inner_text()
        assert 'PRIVATE OLD REQUEST' not in page.locator('body').inner_text()
        assert page.locator('[data-field=prayer]').input_value()==''
    check('Reopening Journal never presents the last saved request',journal_hide)
    def edit_history():
        page.locator('[data-action=browse]').click()
        page.get_by_role('button',name='Patience in a conversation',exact=True).click()
        page.locator('[data-action=edit]').click()
        page.locator('[data-field=prayer]').fill('Father, here is my revised prayer.')
        page.locator('[data-action=save]').click()
        entries=page.evaluate('JSON.parse(localStorage.getItem(WholeheartedJournal.STORAGE)).entries')
        assert entries[0]['revisions'][0]['record']['prayer'].startswith('Father, thank you for clarity')
    check('Editing creates a preserved revision rather than rewriting the original',edit_history)
    def thanks_followup():
        page.locator('#notice [data-action=open-entry]').click()
        before=page.evaluate('localStorage.getItem(WholeheartedJournal.STORAGE)')
        page.locator('[data-action=thank-followup]').click()
        assert page.locator('[data-field=entryType][value=thanksgiving]').is_checked()
        page.locator('details[data-details=record] summary').click()
        assert page.locator('[data-field=answerStatus]').input_value()==''
        page.locator('[data-field=prayer]').fill('Father, thank you for sustaining me while I wait.')
        page.locator('[data-action=save]').click()
        after=page.evaluate('JSON.parse(localStorage.getItem(WholeheartedJournal.STORAGE)).entries')
        original=json.loads(before)['entries'][0]
        assert after[0]['parentId']==original['id']
        assert after[0]['answerStatus']==''
        assert next(x for x in after if x['id']==original['id'])==original
    check('Linked thanksgiving preserves the request and never implies it was answered',thanks_followup)
    def filters():
        page.locator('[data-action=browse]').click()
        page.locator('[data-filter=type]').select_option('thanksgiving')
        assert page.locator('.index-row').count()==1
        page.locator('[data-filter=query]').fill('PRIVATE OLD PRAYER TEXT')
        assert 'No matching entries' in page.locator('#index-results').inner_text()
        page.locator('[data-filter=query]').fill('')
        page.locator('[data-filter=type]').select_option('')
    check('Archive filters work without searching private prayer excerpts',filters)
    def about():
        page.locator('[data-action=about]').click()
        page.locator('#reader summary',has_text='The original poem').click()
        assert page.locator('#reader .poem-line').count()==12
        before=page.evaluate('localStorage.getItem(WholeheartedJournal.STORAGE)')
        page.keyboard.press('Escape')
        assert before==page.evaluate('localStorage.getItem(WholeheartedJournal.STORAGE)')
    check('About keeps the twelve-line poem and never writes journal data',about)
    def type_consistency():
        page.locator('[data-action=learn]').click()
        sizes=page.locator('#reader button.verse-link').evaluate_all('(els)=>els.map(e=>getComputedStyle(e).fontSize)')
        assert len(set(sizes))==1,sizes
        assert sizes[0]=='18px',sizes
        paragraphs=page.locator('#reader .callout p').evaluate_all('(els)=>els.map(e=>getComputedStyle(e).fontSize)')
        assert set(paragraphs)=={'18px'},paragraphs
        page.keyboard.press('Escape')
    check('Equivalent references and teaching paragraphs all render at 18px',type_consistency)
    def catalogue():
        page.locator('nav [data-route=scripture]').click()
        count=page.evaluate('WholeheartedScripture.items.length')
        assert page.locator('.passage-card').count()==count==15
        page.locator('[data-catalogue=query]').fill('Philippians')
        assert page.locator('.passage-card').count()==1
        page.locator('[data-catalogue=query]').fill('')
    check('Scripture page indexes all fifteen registered ranges and supports filtering',catalogue)
    def backup_restore():
        page.locator('nav [data-route=journal]').click();page.locator('[data-action=browse]').click()
        page.locator('summary',has_text='Backup, restore').click()
        with page.expect_download() as ev:page.locator('[data-action=backup]').click()
        ev.value.save_as(OUT/'journal-backup.json')
        original=json.loads((OUT/'journal-backup.json').read_text());extra=original['entries'][0].copy();extra['id']='restored-new';extra['parentId']=None
        original['entries'].append(extra);incoming=OUT/'import-fixture.json';incoming.write_text(json.dumps(original))
        before=page.evaluate('testWrites')
        page.locator('#restore-file').set_input_files(str(incoming))
        page.wait_for_selector('#reader[open]')
        assert page.evaluate('testWrites')==before
        page.locator('[data-action=confirm-restore]').click()
        assert '1 entries restored' in page.locator('#notice').inner_text()
    check('JSON backup/restore requires confirmation and skips existing IDs',backup_restore)
    def no_overflow():
        widths=[320,390,430,768,820,834,1024,1194,1366,1440]
        for width in widths:
            page.set_viewport_size({'width':width,'height':1000})
            for nav in ['journal','scripture']:
                page.locator('nav [data-route='+nav+']').click()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,nav)
            page.locator('[data-action=learn]').click()
            assert page.locator('#reader').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'),(width,'reader')
            page.keyboard.press('Escape')
        page.set_viewport_size({'width':932,'height':430})
        page.locator('[data-action=about]').click()
        assert page.locator('#reader').evaluate('(e)=>e.getBoundingClientRect().height<=innerHeight+1')
        page.keyboard.press('Escape')
    check('Ten responsive widths and landscape fit without horizontal overflow',no_overflow)
    def screenshots():
        page.set_viewport_size({'width':390,'height':844});page.locator('nav [data-route=journal]').click()
        page.screenshot(path=str(OUT/'journal-mobile.png'),full_page=True)
        page.locator('[data-action=learn]').click();page.locator('#reader .callout').first.evaluate('(e)=>e.scrollIntoView({block:"start"})')
        page.screenshot(path=str(OUT/'learn-mobile.png'))
        page.keyboard.press('Escape')
        page.set_viewport_size({'width':834,'height':1112});page.locator('nav [data-route=journal]').click()
        page.screenshot(path=str(OUT/'journal-tablet.png'),full_page=True)
        page.set_viewport_size({'width':1440,'height':1100});page.locator('nav [data-route=pray]').click()
        page.screenshot(path=str(OUT/'prayer-desktop.png'),full_page=True)
        page.locator('nav [data-route=scripture]').click()
        page.screenshot(path=str(OUT/'scripture-desktop.png'),full_page=True)
    check('Mobile, tablet and desktop screenshots captured',screenshots)
    def large_type():
        page.set_viewport_size({'width':390,'height':844});page.locator('[data-action=text-size]').click()
        page.locator('[data-size=larger]').click();page.keyboard.press('Escape')
        page.locator('nav [data-route=journal]').click()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        assert page.locator('[data-field=prayer]').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')>=22
        page.evaluate("document.documentElement.style.fontSize='32px'")
        if not page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'):
            print('OVERFLOW',page.locator('body *').evaluate_all('(els)=>els.filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right,e.textContent.slice(0,80)])'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.locator('[data-action=learn]').click()
        assert page.locator('#reader').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
        page.keyboard.press('Escape')
        page.evaluate("document.documentElement.style.fontSize='';document.documentElement.dataset.reading='standard'")
    check('Reading-size control and 200% root text enlargement remain usable',large_type)
    def quota():
        page.locator('[data-field=prayer]').fill('A prayer that cannot be saved in full storage.')
        page.evaluate('failStorage=true;popupCalls=0');page.locator('[data-action=save]').click()
        assert 'Not saved' in page.locator('#notice').inner_text()
        assert page.locator('[data-field=prayer]').input_value().startswith('A prayer')
        assert page.evaluate('popupCalls')==0
        page.evaluate('failStorage=false')
    check('Storage failure keeps the writing and never opens a falsely saved record',quota)
    def full_limit():
        # Reuse loaded modules; refresh the journal through Browse after fixture injection.
        page.evaluate("""()=>{const J=WholeheartedJournal;const list=Array.from({length:100},(_,i)=>{const d=J.blank('request','2026-09-20T00:00:00Z','limit-'+i);d.prayer='Fixture';return d});localStorage.setItem(J.STORAGE,JSON.stringify({version:3,entries:list}));window.popupCalls=0;}""")
        page.locator('[data-action=browse]').click();page.locator('nav [data-route=journal]').click()
        page.locator('[data-field=prayer]').fill('Please help me at the journal limit.')
        page.locator('[data-action=save]').click()
        assert '100 entries' in page.locator('#notice').inner_text()
        assert page.evaluate('popupCalls')==0
    check('Journal-full error now gives the specific limit and recovery instruction',full_limit)
    def exceptions():
        assert not errors,errors
    check('No browser JavaScript exceptions',exceptions)
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps({'mode':'Chromium DOM injection, simulated localStorage/tab and ESV responses; real Blob downloads','results':results},indent=2))
print('TOTAL',len(results),'passed')
