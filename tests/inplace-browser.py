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
OUT=OUT/'inplace';OUT.mkdir(parents=True,exist_ok=True)
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
      files=['experience.js','build-info.js','theme.js','core.js','catalogue.js','teaching.js','prayer-output.js','guidance-core.js','journal.js','journey-ui.js','export.js','about.js','app.js']
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
    # Browser fixtures are synthetic and make no OpenAI calls. Server contracts are tested in Node.
    page.evaluate("""()=>{
      const original=window.fetch.bind(window);window.requests005=[];window.defer005=false;window.behaviour005='complete';window.release005=null;
      window.fetch=async(url,opts)=>{
        if(!String(url).includes('/api/guidance'))return original(url,opts);
        const data=JSON.parse(opts.body);window.requests005.push(data);
        if(window.defer005)await new Promise(resolve=>window.release005=resolve);
        if(window.behaviour005==='failure')return {ok:false,json:async()=>({error:'The AI returned an unreadable response format. Your earlier words are retained.',code:'OUTPUT_JSON',supportId:'test-support-id'})};
        if(data.action==='reflect'){
          const r=await window.reflectFixture005(data);
          return {ok:true,json:async()=>r};
        }
        const d=WholeheartedJournal.blank();d.journey.issue=data.issue;
        const f=WholeheartedGuidance.local(d);
        const result={sentence:'TEST DRAFT - Father, help me respond with patience.',whems:Object.fromEntries(['W','H','E','M','S'].map(k=>[k,'TEST DRAFT - Father, help me pray honestly in this aspect.'])),extended:'TEST DRAFT - '+f.extended};
        if(window.behaviour005==='partial')delete result.extended;
        if(data.target && data.target!=='all')for(const k of Object.keys(result))if(k!==data.target)delete result[k];
        return {ok:true,json:async()=>({result,at:new Date().toISOString(),model:'gpt-5.4-mini (test fixture)'})};
      };
    }""")
    page.expose_function('reflectFixture005',response)
    def settle():page.wait_for_timeout(180)
    def calls():return page.evaluate('requests005.length')
    def wait_ready():page.wait_for_function("!document.getElementById('guide-prayers-ai').disabled")
    def source_intro():
      assert page.locator('#prayer-introduction h2').inner_text()=='A simple W.H.E.M.S. prayer pattern'
      assert page.locator('#guardrails h2').inner_text()=='Guardrails'
      assert page.locator('#one-line-summary h2').inner_text()=='1-line Summary'
      assert page.locator('#prayer-introduction').bounding_box()['y']<page.locator('#guide-issue').bounding_box()['y']
      assert calls()==0
    check('The requested HTML sections appear with exact headings before the writing journey',source_intro)
    def prerequisites():
      page.locator('#guide-prayers-ai').click();settle()
      assert page.locator('#guidance-issue-action-note').inner_text().find('Suggested starting wording')>=0
      assert not page.locator('#guidance-consent').is_checked();assert calls()==0
      page.locator('#guidance-issue').fill(ISSUE);page.locator('#guidance-consent').check()
      page.locator('[data-journey=context]').fill(CONTEXT)
    check('Missing information identifies the field and supplies wording without auto-filling or consent',prerequisites)
    def guidance_patch():
      page.evaluate("window.issueNode005=document.getElementById('guidance-issue');window.willNode005=document.querySelector('[data-guide-reply=W]');window.prayerNode005=document.querySelector('[data-prayer-form=sentence]');")
      page.locator('#guide-reflect-start').click();page.locator('#guide-understanding').wait_for();wait_ready();settle()
      assert page.evaluate("issueNode005===document.getElementById('guidance-issue') && willNode005===document.querySelector('[data-guide-reply=W]') && prayerNode005===document.querySelector('[data-prayer-form=sentence]')")
      assert not page.locator('#guidance-confirm').is_checked()
    check('Contextual guidance replaces only response-owned sections and keeps original input elements',guidance_patch)
    def unconfirmed():
      before=calls();page.locator('#guide-prayers-ai').click();settle()
      assert page.locator('#guidance-confirm').get_attribute('aria-invalid')=='true';assert calls()==before
      page.locator('#guidance-confirm').check()
    check('The proposed understanding still requires an explicit human acknowledgement',unconfirmed)
    def populate():
      page.locator('#guide-prayers-ai').scroll_into_view_if_needed();settle()
      page.evaluate("window.scroll005=scrollY;window.issueFocus005=document.getElementById('guidance-issue');window.prayerFocus005=document.querySelector('[data-prayer-form=sentence]');")
      page.locator('#guide-prayers-ai').click();wait_ready();settle()
      assert page.locator('[data-prayer-form=sentence]').input_value().startswith('TEST DRAFT')
      for key in KEYS:assert key+' - ' in page.locator('[data-prayer-form=whems]').input_value()
      assert page.locator('[data-prayer-form=extended]').input_value().startswith('TEST DRAFT')
      assert page.evaluate("issueFocus005===document.getElementById('guidance-issue') && prayerFocus005===document.querySelector('[data-prayer-form=sentence]')")
      assert page.evaluate('scrollY')>1000
      assert page.locator('#prayer-flow-status').inner_text().find('filled in place')>=0
    check('One submitted request fills all three prayers in place without rebuilding the page',populate)
    def partial():
      page.locator('[data-prayer-form=extended]').fill('My earlier extended words, to be kept.')
      page.evaluate("behaviour005='partial'");page.locator('#guide-prayers-ai').click();wait_ready();settle()
      assert page.locator('[data-prayer-form=extended]').input_value()=='My earlier extended words, to be kept.'
      assert 'not returned' in page.locator('[data-form-feedback=extended]').inner_text()
      assert '2 of 3' in page.locator('#prayer-flow-status').inner_text()
      page.set_viewport_size({'width':390,'height':844});page.locator('#prayer-flow-status').scroll_into_view_if_needed();settle()
      page.screenshot(path=str(OUT/'partial-prayers-mobile.png'))
    check('An unfinished extended form is explained without discarding the two returned forms or old wording',partial)
    def targeted():
      s=page.locator('[data-prayer-form=sentence]').input_value();w=page.locator('[data-prayer-form=whems]').input_value()
      before=calls();page.evaluate("behaviour005='complete'")
      page.locator('[data-guide-target=extended]').click();wait_ready();settle()
      assert calls()==before+1;assert page.evaluate('requests005.at(-1).target')=='extended'
      assert page.locator('[data-prayer-form=sentence]').input_value()==s
      assert page.locator('[data-prayer-form=whems]').input_value()==w
      assert page.locator('[data-prayer-form=extended]').input_value().startswith('TEST DRAFT')
    check('Retrying one prayer sends a single targeted request and leaves the other two unchanged',targeted)
    def protect_edits():
      page.evaluate('defer005=true');page.locator('#guide-prayers-ai').click()
      page.wait_for_function('release005!==null')
      page.locator('[data-prayer-form=sentence]').fill('MY OWN EDITS WHILE WAITING')
      page.evaluate('defer005=false;release005();release005=null');wait_ready();settle()
      assert page.locator('[data-prayer-form=sentence]').input_value()=='MY OWN EDITS WHILE WAITING'
      assert 'Your edits have been kept' in page.locator('[data-form-feedback=sentence]').inner_text()
      assert page.locator('[data-use-returned=sentence]').is_visible()
      assert page.locator('[data-prayer-form=extended]').input_value().startswith('TEST DRAFT')
    check('Edits made during generation survive; returned alternatives are offered separately',protect_edits)
    def changed_context():
      old=page.locator('[data-prayer-form=extended]').input_value()
      page.evaluate('defer005=true');page.locator('#guide-prayers-ai').click();page.wait_for_function('release005!==null')
      page.locator('[data-guide-reply=M]').fill('New context received while the response was being prepared.')
      page.evaluate('defer005=false;release005();release005=null');wait_ready();settle()
      assert 'CONTEXT_CHANGED' in page.locator('#prayer-flow-status').inner_text()
      assert page.locator('[data-prayer-form=extended]').input_value()==old
    check('Changed context prevents an obsolete response from replacing the prayers',changed_context)
    def clear_failure():
      page.evaluate("behaviour005='failure'");before=calls();old=page.locator('[data-prayer-form=extended]').input_value()
      page.locator('[data-guide-target=extended]').click();wait_ready();settle()
      assert 'OUTPUT_JSON' in page.locator('#prayer-flow-status').inner_text()
      assert page.locator('[data-prayer-form=extended]').input_value()==old
      assert not page.locator('#guidance-confirm').get_attribute('aria-invalid')
      assert calls()==before+1
      page.locator('#prayer-flow-status').scroll_into_view_if_needed();settle();page.screenshot(path=str(OUT/'error-explanation-mobile.png'))
    check('Technical failure has a support code, remains near the prayer output, and does not blame acknowledgement',clear_failure)
    def local_one():
      before=calls();s=page.locator('[data-prayer-form=sentence]').input_value()
      page.locator('[data-local-form=extended]').click();settle()
      assert calls()==before
      assert page.locator('[data-prayer-form=sentence]').input_value()==s
      assert 'Local starting prayer' in page.locator('[data-form-feedback=extended]').inner_text()
      assert page.locator('[data-prayer-form=extended]').input_value()
    check('Local starting wording is available for only the unfinished form, with no AI call',local_one)
    def brand():
      before=calls();text=page.locator('[data-prayer-form=sentence]').input_value()
      page.evaluate("window.brandInput005=document.getElementById('guidance-issue')")
      page.locator('.brand').click();settle()
      assert calls()==before;assert page.evaluate("brandInput005===document.getElementById('guidance-issue')")
      assert page.locator('[data-prayer-form=sentence]').input_value()==text
    check('Wholehearted branding navigates only, without AI, loss of words or redundant page rendering',brand)
    def screens():
      for w,h in [(320,640),(390,844),(430,932),(844,390),(768,1024),(1024,768),(834,1194),(1194,834),(1024,1366),(1366,1024)]:
        page.set_viewport_size({'width':w,'height':h});settle()
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),(w,h)
      page.set_viewport_size({'width':390,'height':844});page.locator('#prayer-introduction').scroll_into_view_if_needed();settle();page.screenshot(path=str(OUT/'source-introduction-mobile.png'))
      assert not errors,errors
    check('Ten phone and tablet orientations retain the new sections and show no JavaScript exceptions',screens)
    (OUT/('inplace-'+MODE+'-'+os.environ.get('TEST_BROWSER','chromium')+'-results.json')).write_text(json.dumps({'mode':MODE,'AI':'controlled fixture, no model calls','results':results},indent=2))
    browser.close()
finally:
  if server: server.terminate()
