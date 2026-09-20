"""Completion UI regression. HTTP mode uses a real local web server and browser storage.
AI responses are explicitly test fixtures, never live OpenAI output. LIVE_ESV=1 checks
Crossway's real iframe. DOM mode is for environments that prohibit navigation; it uses
injected assets and simulated storage. Both modes produce actual download files.
"""
import json, os, re, socket, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('EVIDENCE_DIR', str(ROOT/'evidence')))
OUT.mkdir(parents=True,exist_ok=True)
MODE=os.environ.get('BROWSER_MODE','http')
LIVE=os.environ.get('LIVE_ESV')=='1'
results=[]; api_calls=[]; errors=[]
REFS=['luke-22-42','psalm-139-23-24','matthew-26-37-39','romans-12-1-2','ephesians-2-8-10']
KEYS=['W','H','E','M','S']
ISSUE='Should I talk to my daughter or pray while her research learning curve is steep?'
CONTEXT='She is an adult and has welcomed contact. I do not yet know what support she wants.'
def check(name, fn):
    if MODE != 'dom' and fn.__name__ in {'cancel','storage_fail'}:
        results.append({'test':name,'result':'Skipped','reason':'Covered in DOM error-fixture run; not repeated in native HTTP run.'});print('SKIP',name,flush=True);return
    fn(); results.append({'test':name,'result':'Passed'});print('PASS',name,flush=True)
def response(data):
    listen='listen, not advise' in json.dumps(data)
    r={'summary':'TEST FIXTURE: You are considering support through prayer and a listening conversation.',
       'statedFacts':['TEST FIXTURE: Your adult daughter has welcomed contact.'],
       'uncertainties':['TEST FIXTURE: What support has she requested?'],
       'clarification':'What has your daughter actually asked you to do?',
       'areas':[{'key':k,'focus':'TEST FIXTURE: Supporting your daughter in this aspect.',
                 'question':('How can you listen without giving unsolicited advice?' if listen and k=='W' else f'TEST FIXTURE: What does {k} invite you to consider in this research-year concern?'),
                 'followup':'Use only what she has said, not an assumed motive.', 'referenceIds':[REFS[i]]} for i,k in enumerate(KEYS)],
       'options':([{'action':'Offer to listen without advice.','reason':'She explicitly asked to be heard.','caution':'Ask before offering solutions.','referenceIds':['proverbs-15-22']}] if listen else []),
       'safetyNote':''}
    return {'result':r,'model':'gpt-5.4-mini (test fixture)','at':'2026-09-20T10:00:00Z'}
server=None
if MODE=='http':
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(ROOT/'public')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    URL=f'http://127.0.0.1:{port}/';time.sleep(.3)
else: URL='https://fixture.invalid/'
try:
  with sync_playwright() as pw:
    kwargs={'args':['--no-sandbox']}
    if os.environ.get('CHROMIUM_PATH'): kwargs['executable_path']=os.environ['CHROMIUM_PATH']
    elif MODE=='dom': kwargs['executable_path']='/usr/bin/chromium'
    browser=pw.chromium.launch(**kwargs)
    ctx=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=ctx.new_page();page.set_default_timeout(8000)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept())
    def api(route):
      data=route.request.post_data_json;api_calls.append(data)
      if data['action']=='reflect': route.fulfill(status=200,json=response(data))
      else:
       # Deliberately a contract fixture, not a theological model evaluation.
       d=page.evaluate('()=>{const d=WholeheartedJournal.blank();d.journey.issue="Test concern";return d;}')
       # API fixture long prayer is fabricated test text, visibly labelled.
       forms={'sentence':'TEST FIXTURE: Father, help me listen with patience and pray faithfully.',
              'whems':'\n\n'.join(k+' - '+n+'\nTEST FIXTURE: help me respond faithfully.' for k,n in zip(KEYS,['Will','Heart','Emotions','Mind','Soul'])),
              'extended':'\n\n'.join(['TEST FIXTURE - not a historical prayer. '+('Father, teach me to listen with patience and wisdom. '*13)]*5)}
       route.fulfill(status=200,json={'result':forms,'model':'gpt-5.4-mini (fixture)','at':'2026-09-20T10:00:00Z'})
    def source(route):
      id=route.request.url.split('id=')[-1]
      route.fulfill(status=200,json={'id':id,'translation':'ESV','mode':'crossway-embed'})
    if MODE=='http':
      page.route('**/api/guidance',api);page.route('**/api/scripture?*',source)
      if not LIVE: ctx.route('https://www.esv.org/crossref/**',lambda r:r.fulfill(body='<p>Crossway transport fixture - not Bible text.</p>',content_type='text/html'))
      page.goto(URL,wait_until='networkidle')
    else:
      html=(ROOT/'public/index.html').read_text();html=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S);html=re.sub(r'<link\b[^>]*>','',html)
      page.set_content(html);page.add_style_tag(content=(ROOT/'public/styles.css').read_text())
      page.evaluate("""()=>{const data={};window.testWrites=0;window.apiCalls=[];window.failAPI=false;window.failStorage=false;window.delayAPI=false;
      Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.hasOwn(data,k)?data[k]:null,setItem:(k,v)=>{if(window.failStorage)throw Error('quota');window.testWrites++;data[k]=String(v);},snapshot:()=>({...data})}});
      window.open=()=>null;
      }""")
      files=['build-info.js','theme.js','core.js','catalogue.js','guidance-core.js','journal.js','journey-ui.js','export.js','about.js','app.js']
      for name in files:page.add_script_tag(content=(ROOT/'public'/name).read_text())
      page.expose_function('fixture_response',response)
      page.evaluate("""()=>{window.fetch=async(url,opts)=>{
        if(String(url).includes('/api/scripture'))return {ok:true,json:async()=>({id:String(url).split('id=')[1],translation:'ESV',mode:'crossway-embed'})};
        const data=JSON.parse(opts.body);window.apiCalls.push(data);
        if(window.failAPI)return {ok:false,json:async()=>({error:'Test provider unavailable.'})};
        if(window.delayAPI)return await new Promise((resolve,reject)=>opts.signal.addEventListener('abort',()=>reject(new DOMException('Cancelled','AbortError'))));
        if(data.action==='reflect')return {ok:true,json:async()=>await window.fixture_response(data)};
        const d=WholeheartedJournal.blank();d.journey.issue=data.issue;d.journey.replies=data.replies;const forms=WholeheartedGuidance.local(d);forms.origin='Test fixture';
        return {ok:true,json:async()=>({result:forms,model:'gpt-5.4-mini (fixture)',at:new Date().toISOString()})};
      };}""")
    def count_calls():return len(api_calls) if MODE=='http' else page.evaluate('apiCalls.length')
    def opened():
      assert page.locator('.open-area').count()==5
      for key in KEYS: assert page.locator(f'#reflection-{key} textarea[data-guide-reply]').is_visible()
      assert page.locator('[data-prayer-form]').count()==3
      assert 'Build 0.0.002' in page.locator('body').inner_text()
    check('All five contextual areas and all three final prayer forms are open',opened)
    def consent():
      page.locator('[data-journey=issue]').fill(ISSUE);page.locator('[data-journey=context]').fill(CONTEXT)
      page.locator('[data-guide-action=reflect]').first.click()
      assert 'consent' in page.locator('#notice').inner_text().lower();assert count_calls()==0
      page.locator('[data-guidance-consent]').check();page.locator('[data-guide-action=reflect]').first.click()
      page.locator('.interpretation').wait_for();assert count_calls()==1
      assert 'TEST FIXTURE' in page.locator('.interpretation').inner_text()
      assert page.locator('.context-focus').count()==5
    check('No AI call before consent; submitted issue produces five displayed contextual questions',consent)
    def adapt():
      page.locator('[data-guide-reply=W]').fill('She asked me to listen, not advise.')
      page.locator('[data-guide-reply=H]').fill('I hope she knows she is loved, not judged.')
      page.locator('[data-guide-reply=E]').fill('I feel concerned.')
      page.locator('[data-guide-action=reflect]').last.click()
      page.get_by_text('How can you listen without giving unsolicited advice?',exact=True).wait_for()
      assert 'Offer to listen without advice.' in page.locator('.decision-paper').inner_text()
      assert page.locator('[data-guide-reply=W]').input_value()=='She asked me to listen, not advise.'
      assert count_calls()==2
    check('New replies are sent and updated guidance/options replace the earlier proposal',adapt)
    def confirm_prayers():
      page.locator('[data-guide-action=prayers]').click()
      assert 'confirm' in page.locator('#notice').inner_text().lower();assert count_calls()==2
      page.locator('[data-journey-confirm]').check()
      page.locator('[data-field=nextStep]').fill('Offer a listening conversation at a time that suits her.')
      page.locator('[data-field="areas.W.thank"]').check()
      page.locator('[data-field="areas.W.thankNote"]').fill('willingness to pause')
      page.locator('[data-field="areas.W.ask"]').check()
      page.locator('[data-field="areas.W.askNote"]').fill('listen without taking over')
      page.locator('[data-guide-action=prayers]').click()
      page.wait_for_function("document.querySelector('[data-prayer-form=extended]').value.length>1500")
      assert count_calls()==3
      for key in ['sentence','whems','extended']:assert page.locator(f'[data-prayer-form={key}]').input_value()
    check('Confirmed understanding leads to all three prayer forms without losing mixed notes',confirm_prayers)
    def edit_copy():
      old=page.locator('[data-prayer-form=extended]').input_value()
      page.locator('[data-prayer-form=sentence]').fill('Father, help me listen with love and patience.')
      assert page.locator('[data-prayer-form=extended]').input_value()==old
    check('Editing one prayer leaves the other two unchanged',edit_copy)
    def verse():
      page.locator('#reflection-W [data-verse]').first.click()
      frame=page.locator('#reader iframe.esv-reader-frame');frame.wait_for()
      assert frame.get_attribute('src').startswith('https://www.esv.org/crossref/')
      assert frame.get_attribute('referrerpolicy')=='no-referrer'
      assert not frame.get_attribute('src').find('daughter')>=0
      if LIVE:
        f=page.frame_locator('#reader iframe')
        f.locator('#passage-text').wait_for(timeout=20000)
        assert len(f.locator('#passage-text').inner_text())>30
        assert f.locator('.verse-num').count()>0
      page.locator('#reader [data-action=attach-ref]').click()
      assert 'Reference added' in page.locator('.reader-feedback').inner_text()
      page.locator('#reader [data-verse]').first.click()
      page.locator('#reader [data-action=reader-back]').click()
      page.locator('#reader [data-action=reader-close]').click()
      assert page.locator('[data-prayer-form=sentence]').input_value()=='Father, help me listen with love and patience.'
    check('Crossway in-page reader, cross-reference Back and focus return preserve the prayer',verse)
    def saved():
      if MODE=='http':
        with ctx.expect_page() as event:page.locator('[data-action=save]').click()
        tab=event.value;tab.wait_for_load_state();tab.locator('[data-action=download-html]').first.wait_for()
        assert 'ready to download' in tab.locator('body').inner_text()
        with tab.expect_download() as dl:tab.locator('[data-action=download-html]').first.click()
        dl.value.save_as(OUT/'saved-three-prayers.html');tab.close()
      else:
        page.locator('[data-action=save]').click()
        assert 'Saved on this device' in page.locator('#notice').inner_text()
        with page.expect_download() as dl:page.locator('#notice [data-action=download-html]').click()
        dl.value.save_as(OUT/'saved-three-prayers.html')
      content=(OUT/'saved-three-prayers.html').read_text()
      for text in ['One-sentence prayer','W.H.E.M.S. prayer','Extended prayer',ISSUE,'Father, help me listen with love and patience.']:assert text in content,text
      assert '<script' not in content
      stored=page.evaluate("JSON.parse(localStorage.getItem('wholehearted-journal-v3'))")
      assert len(stored['entries'])==1
      assert stored['entries'][0]['prayerForms']['sentence']=='Father, help me listen with love and patience.'
    check('Save, separate download page and real HTML download preserve all three forms',saved)
    def journal_private():
      page.locator('nav [data-route=journal]').click()
      assert page.locator('[data-field=prayer]').input_value()==''
      assert ISSUE not in page.locator('body').inner_text()
      page.locator('[data-action=browse]').click()
      assert 'listen with love and patience' not in page.locator('body').inner_text()
      page.locator('[data-action=open-entry]').first.click()
      assert 'One-sentence prayer' in page.locator('body').inner_text()
      page.locator('[data-action=edit]').click()
      assert page.locator('[data-prayer-form=sentence]').input_value()=='Father, help me listen with love and patience.'
      page.locator('[data-prayer-form=sentence]').fill('Father, help me listen with gentleness.')
      if MODE=='http':
        with ctx.expect_page() as event:page.locator('[data-action=save]').click()
        event.value.close()
      else:page.locator('[data-action=save]').click()
      record=page.evaluate("JSON.parse(localStorage.getItem('wholehearted-journal-v3')).entries[0]")
      assert len(record['revisions'])==1
      assert record['revisions'][0]['record']['prayerForms']['sentence']=='Father, help me listen with love and patience.'
    check('Journal hides old content until Browse and preserves revisions of all forms',journal_private)
    def reload():
      if MODE=='http':page.reload(wait_until='networkidle')
      page.locator('nav [data-route=journal]').click();assert ISSUE not in page.locator('body').inner_text()
      assert page.evaluate("JSON.parse(localStorage.getItem('wholehearted-journal-v3')).entries.length")==1
    check('Saved record remains readable after reload (native storage in HTTP mode)',reload)
    def follow():
      page.locator('[data-action=browse]').click();page.locator('[data-action=open-entry]').first.click()
      page.locator('[data-action=thank-followup]').click()
      assert page.locator('[data-journey=issue]').input_value()==ISSUE
      assert page.locator('[data-prayer-form=sentence]').input_value()==''
      assert page.locator('[data-field=answerStatus]').input_value()==''
      page.locator('[data-journey=context]').fill('She welcomed the conversation. The research is still demanding.')
      page.locator('[data-guide-action=local]').click()
      assert page.locator('[data-prayer-form=extended]').input_value()
      page.locator('[data-guide-action=historic]').click()
      assert page.locator('#reader').get_by_text('Early Church · Augustine',exact=True).is_visible()
      page.locator('#reader [data-action=reader-close]').click()
    check('Linked thanksgiving preserves original request and can create all forms locally',follow)
    def cancel():
      if MODE!='dom':return
      page.locator('[data-guidance-consent]').check();page.evaluate('window.delayAPI=true')
      page.locator('[data-guide-action=reflect]').first.click()
      page.locator('[data-guide-action=cancel]').click()
      page.wait_for_function("document.querySelector('#notice').textContent.includes('cancelled')")
      assert page.locator('[data-journey=issue]').input_value()==ISSUE
      page.evaluate('window.delayAPI=false;window.failAPI=true')
      page.locator('[data-guide-action=reflect]').first.click()
      page.wait_for_function("document.querySelector('#notice').textContent.includes('unavailable')")
      assert page.locator('[data-journey=issue]').input_value()==ISSUE
      page.evaluate('window.failAPI=false')
    check('Cancelled/unavailable AI retains earlier writing (DOM error fixture)',cancel)
    def viewport():
      for w in [320,390,430,768,820,834,1024,1194,1366,1440]:
        page.set_viewport_size({'width':w,'height':950})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),w
      page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)')
      page.screenshot(path=str(OUT/'guided-mobile.png'))
      page.locator('#reflection-W').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'whems-mobile.png'))
      page.set_viewport_size({'width':1440,'height':1000});page.locator('.final-prayers').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'three-prayers-desktop.png'))
      page.set_viewport_size({'width':932,'height':430});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    check('Ten widths, narrow screens and landscape retain open guidance without overflow',viewport)
    def zoom_about():
      page.set_viewport_size({'width':390,'height':844})
      page.evaluate("document.documentElement.style.fontSize='200%'")
      assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
      page.evaluate("document.documentElement.style.fontSize=''")
      page.locator('[data-action=about]').click()
      assert page.locator('.poem-line').count()==12
      assert 'Optional contextual guidance uses AI' in page.locator('#reader').inner_text()
      page.keyboard.press('Escape')
    check('Enlarged text, original poem and updated About remain usable',zoom_about)
    def storage_fail():
      if MODE!='dom':return
      old=page.evaluate("localStorage.getItem('wholehearted-journal-v3')")
      page.evaluate('window.failStorage=true');page.locator('[data-action=save]').click()
      assert 'Not saved' in page.locator('#notice').inner_text()
      assert old==page.evaluate("localStorage.getItem('wholehearted-journal-v3')")
      page.evaluate('window.failStorage=false')
    check('Storage failure does not falsely report success or discard the prayer (DOM fixture)',storage_fail)
    check('No application JavaScript exceptions',lambda: (_ for _ in ()).throw(AssertionError(errors)) if errors else None)
    browser.close()
finally:
  if server:server.terminate();server.wait(timeout=5)
  (OUT/f'completion-{MODE}-results.json').write_text(json.dumps({'mode':MODE,'ai':'Contract fixture, not real OpenAI generation','live_esv':LIVE,'results':results},indent=2))
