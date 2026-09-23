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
OUT=OUT/'experience';OUT.mkdir(parents=True,exist_ok=True)
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
    engine=os.environ.get('TEST_BROWSER','chromium')
    kwargs={'args':['--no-sandbox']} if engine=='chromium' else {}
    if engine=='chromium':
      if os.environ.get('CHROMIUM_PATH'): kwargs['executable_path']=os.environ['CHROMIUM_PATH']
      elif MODE=='dom': kwargs['executable_path']='/usr/bin/chromium'
    browser=getattr(pw,engine).launch(**kwargs)
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
      page.set_content(html);page.add_style_tag(content=(ROOT/'public/styles.css').read_text());page.add_style_tag(content=(ROOT/'public/experience.css').read_text())
      page.evaluate("""()=>{const data={};window.testWrites=0;window.apiCalls=[];window.failAPI=false;window.failStorage=false;window.delayAPI=false;
      Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.hasOwn(data,k)?data[k]:null,setItem:(k,v)=>{if(window.failStorage)throw Error('quota');window.testWrites++;data[k]=String(v);},snapshot:()=>({...data})}});
      window.open=()=>null;
      }""")
      files=['experience.js','build-info.js','theme.js','core.js','catalogue.js','guidance-core.js','journal.js','journey-ui.js','export.js','about.js','app.js']
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
    def settled():page.wait_for_timeout(160)
    def focus_is(sel):page.wait_for_function('(s)=>document.activeElement===document.querySelector(s)',arg=sel)
    def fits(sel):
      r=page.locator(sel).bounding_box();vp=page.viewport_size
      assert r and r['x']>=-1 and r['x']+r['width']<=vp['width']+1,(sel,r)
    def blocked_from_bottom():
      page.set_viewport_size({'width':390,'height':844})
      page.locator('#guide-prayers-ai').click();settled()
      assert page.locator('.action-feedback li').count()==2
      assert page.locator('#guidance-issue').get_attribute('aria-invalid')=='true'
      focus_is('#guidance-issue');assert count_calls()==0
      assert not page.locator('#guidance-consent').is_checked()
      assert float(page.locator('.action-feedback').evaluate('(e)=>getComputedStyle(e).borderTopWidth').replace('px',''))>=2
      assert 0<=page.locator('#guidance-issue').bounding_box()['y']<200
    check('Blocked AI at the bottom identifies every prerequisite and focuses the first missing field',blocked_from_bottom)
    def resolve_consent():
      page.locator('#guidance-issue').fill(ISSUE);settled()
      assert page.locator('.action-feedback li').count()==1
      page.locator('#guidance-issue-action-note [data-locate]').click();settled();focus_is('#guidance-consent')
      note=page.locator('#guidance-consent-action-note');assert note.is_visible()
      assert 'guidance-consent-action-note' in page.locator('#guidance-consent').get_attribute('aria-describedby')
      page.screenshot(path=str(OUT/'consent-mobile.png'))
      page.locator('#guidance-consent').check();settled();assert count_calls()==0
      assert 'complete' in note.inner_text()
      note.locator('[data-return-origin]').click();settled();focus_is('#guide-prayers-ai')
      assert not page.locator('#guidance-consent').get_attribute('aria-invalid')
    check('Human consent clears its own error and offers a return, without an automatic AI call',resolve_consent)
    def contextual():
      page.locator('[data-journey=context]').fill(CONTEXT)
      page.locator('#guide-reflect-start').click();page.locator('#guide-understanding').wait_for();settled()
      assert count_calls()==1
      assert page.locator('.guidance-source').count()==5
      assert not page.locator('#guidance-confirm').is_checked()
      assert page.locator('[data-guide-reply=W]').get_attribute('placeholder').startswith('TEST FIXTURE')
      assert page.locator('.reflection-choice input:checked').count()==0
    check('Contextual results change the questions and writing hints but not personal checkboxes',contextual)
    def acknowledgement():
      page.locator('#guide-prayers-ai').click();settled();focus_is('#guidance-confirm')
      assert page.locator('.action-feedback li').count()==1
      assert page.locator('#guidance-confirm').get_attribute('aria-invalid')=='true'
      assert not page.locator('#guidance-confirm').is_checked();assert count_calls()==1
      assert page.locator('#guidance-confirm-action-note').is_visible()
      page.screenshot(path=str(OUT/'acknowledgement-mobile.png'))
      page.locator('#guidance-confirm').check();settled();assert count_calls()==1
      page.locator('#guidance-confirm-action-note [data-return-origin]').click();settled();focus_is('#guide-prayers-ai')
      # Editing the understanding must invalidate the earlier acknowledgement again.
      page.locator('#guidance-summary').fill('Corrected: I want to listen before offering any advice.');settled()
      assert not page.locator('#guidance-confirm').is_checked()
      assert page.locator('.action-feedback li').count()==1
      page.locator('#guidance-confirm').check();settled()
      page.locator('#guide-prayers-ai').click()
      page.wait_for_function("document.querySelector('[data-prayer-form=extended]').value.length>1500")
      assert count_calls()==2
    check('Acknowledgement is pinpointed, corrected and deliberately resubmitted; edits invalidate stale agreement',acknowledgement)
    def fields_preserved():
      page.locator('[data-field="areas.W.thank"]').check()
      page.locator('[data-field="areas.W.thankNote"]').fill('willingness to listen')
      page.locator('[data-field="areas.W.ask"]').check()
      page.locator('[data-field="areas.W.askNote"]').fill('patience')
      page.locator('[data-guide-reply=W]').fill('She asked me to listen, not advise.')
      text=page.locator('[data-prayer-form=sentence]').input_value()
      page.locator('#guide-reflect-followup').click()
      page.get_by_text('How can you listen without giving unsolicited advice?',exact=True).wait_for();settled()
      assert page.locator('[data-field="areas.W.thank"]').is_checked()
      assert page.locator('[data-field="areas.W.ask"]').is_checked()
      assert page.locator('[data-field="areas.W.askNote"]').input_value()=='patience'
      assert page.locator('[data-prayer-form=sentence]').input_value()==text
      assert page.locator('[data-guide-reply=W]').get_attribute('placeholder')=='How can you listen without giving unsolicited advice?'
      page.evaluate("WholeheartedExperience.reveal('#reflection-W')");settled()
      page.screenshot(path=str(OUT/'contextual-will-mobile.png'))
    check('A new reply updates contextual prompts while preserving mixed notes and all prayer edits',fields_preserved)
    def toc():
      before=page.locator('[data-field="areas.W.askNote"]').input_value()
      page.locator('[data-fab=contents]').click();assert page.locator('#reader').is_visible()
      page.wait_for_function("document.getElementById('page-tools').hidden")
      assert page.locator('.page-contents button').count()==16
      page.screenshot(path=str(OUT/'contents-mobile.png'))
      page.locator('.page-contents [data-locate="#guide-save"]').click();settled()
      assert not page.locator('#reader').is_visible();focus_is('#guide-save')
      assert page.locator('[data-field="areas.W.askNote"]').input_value()==before
      assert not page.locator('#page-tools').is_hidden()
    check('Contents includes the actual journey and returns to the chosen section without erasing writing',toc)
    def arrows():
      page.emulate_media(reduced_motion='reduce')
      page.evaluate('scrollTo(0,1000)');settled();before=page.evaluate('scrollY')
      page.locator('[data-fab=down]').click();settled();after=page.evaluate('scrollY');assert after>before+100
      page.locator('[data-fab=up]').click();settled();assert page.evaluate('scrollY')<after-100
    check('Up and Down move one visible screen and respect reduced-motion preference',arrows)
    def orientations():
      for w,h in [(320,640),(390,844),(430,932),(768,1024),(820,1180),(834,1194),(1024,1366),(1366,1024),(932,430),(844,390)]:
        page.set_viewport_size({'width':w,'height':h});settled()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(w,h)
        fits('#page-tools')
        for s in ['contents','up','down']:
          r=page.locator(f'[data-fab={s}]').bounding_box();assert r['height']>=44 and r['width']>=44
        page.locator('#guide-prayers-ai').click();settled();focus_is('#guidance-confirm')
        r=page.locator('#guidance-confirm').bounding_box();assert 0<=r['y']<h-60,(w,h,r)
      page.set_viewport_size({'width':932,'height':430});settled();assert page.locator('#guidance-confirm').bounding_box()['y']>=0;page.screenshot(path=str(OUT/'acknowledgement-landscape.png'))
      page.set_viewport_size({'width':1024,'height':1366});settled();page.screenshot(path=str(OUT/'acknowledgement-tablet.png'))
    check('Ten portrait/landscape sizes keep controls touchable and route errors to visible fields',orientations)
    def text_size():
      page.set_viewport_size({'width':390,'height':844});page.evaluate("document.documentElement.style.fontSize='200%'");settled()
      fits('#page-tools');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
      page.locator('[data-fab=contents]').click();fits('#reader');page.keyboard.press('Escape')
      page.evaluate("document.documentElement.style.fontSize=''");settled()
    check('Two-hundred-percent text remains readable without horizontal page overflow',text_size)
    def keyboard_geometry():
      # Explicit viewport fixture: this is not a physical Apple keyboard test.
      page.set_viewport_size({'width':390,'height':844});page.locator('[data-guide-reply=H]').focus()
      page.evaluate("""()=>{window.originalVV=visualViewport;Object.defineProperty(window,'visualViewport',{configurable:true,value:{width:390,height:340,offsetTop:0,offsetLeft:0,scale:1}});dispatchEvent(new Event('resize'));}""")
      settled();assert page.locator('html').get_attribute('data-keyboard')=='true'
      r=page.locator('#page-tools').bounding_box();assert r['y']+r['height']<=340
      assert page.locator('[data-fab=up]').is_hidden()
      page.evaluate("Object.defineProperty(window,'visualViewport',{configurable:true,value:originalVV});dispatchEvent(new Event('resize'))");settled()
      assert not page.locator('[data-fab=up]').is_hidden()
    check('Keyboard-shrink fixture moves navigation above the keyboard and restores it afterwards',keyboard_geometry)
    def notices():
      page.evaluate("document.activeElement.blur();scrollTo(0,1900);WholeheartedExperience.notify('Your writing has been kept. Please review the next step.');")
      settled();assert abs(page.evaluate('scrollY')-1900)<2
      fits('#notice');r=page.locator('#notice').bounding_box();assert 0<=r['y']<100
      assert page.locator('#notice').evaluate('(e)=>getComputedStyle(e).borderTopStyle')=='solid'
      page.locator('.notice-dismiss').click();assert page.locator('#notice').is_hidden()
    check('Bordered status stays in the viewport without scrolling the long page to its footer',notices)
    def no_auto():
      calls=count_calls()
      page.locator('[data-guide-reply=E]').fill('I feel concerned but want to listen.')
      page.set_viewport_size({'width':844,'height':390});settled()
      assert count_calls()==calls
      if MODE=='dom':assert page.evaluate('testWrites')==0
      assert len(errors)==0,errors
    check('Typing, navigation and rotation do not send requests, save prayers or raise JavaScript errors',no_auto)
    browser.close()
finally:
  if server:server.terminate();server.wait(timeout=5)
  (OUT/f'experience-{MODE}-{os.environ.get("TEST_BROWSER","chromium")}-results.json').write_text(json.dumps({'mode':MODE,'ai':'Controlled fixture, no chargeable API requests','virtual_keyboard':'VisualViewport geometry fixture, not native device','results':results},indent=2))
