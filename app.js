/* Browser UI. User reflections are never sent to a server or a source website. */
(function () {
  'use strict';
  const C=window.WholeheartedCore, X=window.WholeheartedExport, main=document.getElementById('main');
  const storage={getItem:k=>localStorage.getItem(k),setItem:(k,v)=>localStorage.setItem(k,v)};
  let journal=C.read(storage), draft=null, area='W', dirty=false, route='home';
  const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link=(url,label)=>`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} <span aria-hidden="true">↗</span></a>`;
  const btn=(action,label,kind='secondary',extra='')=>`<button type="button" class="${kind}" data-action="${action}" ${extra}>${label}</button>`;
  const field=(key,label,value,placeholder='',rows=3,max=2000)=>`<label class="field" for="f-${key}">${label}<textarea id="f-${key}" data-field="${key}" rows="${rows}" maxlength="${max}" placeholder="${esc(placeholder)}">${esc(value)}</textarea></label>`;
  const refs=a=>`<div class="refs">${link(C.esv(a.passage),a.passage+' · ESV')}${link(C.step(a.step),'STEP study')}${link('https://www.blueletterbible.org/esv/'+a.blb+'/','Blue Letter Bible')}</div>`;
  const status=a=>a.thank&&a.ask?'Thanks + help':a.thank?'Thanksgiving':a.ask?'Request for help':'Not recorded';
  const date=s=>{const d=new Date(s);return Number.isNaN(d.getTime())?'Date not available':new Intl.DateTimeFormat('en-SG',{dateStyle:'medium',timeStyle:'short',timeZone:'Asia/Singapore'}).format(d)+' SGT';};
  function notify(message) { const el=document.getElementById('notice');el.textContent=message;el.hidden=!message; }
  function refresh(){journal=C.read(storage);if(!journal.ok)notify(journal.error);}
  function go(next,replace=false){route=next;history[replace?'replaceState':'pushState'](null,'','#'+next);render();}
  function focus(){const h=main.querySelector('h1');if(h){h.tabIndex=-1;h.focus({preventScroll:true});}window.scrollTo(0,0);}
  function title(kicker,heading,body){return `<div class="heading"><p class="eyebrow">${kicker}</p><h1>${heading}</h1><p class="intro">${body}</p></div>`;}
  function home(){return `<section class="home-grid"><div class="hero">${title('A little space for prayer','Bring it all<br>before God.','The part that is grateful. The part that is struggling.<br>There is room for both in your prayer.')}<div class="actions">${btn('new','Seek God’s help <span aria-hidden="true">→</span>','primary')}${btn('thanks','Give thanks')}</div><p class="fine">No login. No AI. Save only when you choose.</p>${draft?btn('resume','Continue current prayer','quiet'):''}</div><aside class="illustration"><p class="eyebrow">One prayer. Both truths.</p><div class="example"><span class="example-icon" aria-hidden="true">+</span><div><h2>Father, thank you…</h2><p>for helping me understand what is right.</p></div></div><div class="example"><span class="example-icon" aria-hidden="true">↗</span><div><h2>Please help me…</h2><p>respond with love while I am still hurt.</p></div></div><p class="fine">An example, not an assessment of your life.</p>${link(C.esv('Philippians 4:6-7'),'Prayer with thanksgiving')}</aside></section><section class="overview" aria-labelledby="whole-title"><div><p class="eyebrow">The whole person, before God</p><h2 id="whole-title">Five invitations. Not five scores.</h2></div><div class="five">${C.AREAS.map(a=>`<div><b>${a.key}</b><span>${a.name}</span></div>`).join('')}</div><p>${esc(C.DESCRIPTION)}</p></section><div class="home-bottom"><p><strong>You do not have to feel settled to begin.</strong><br>Thank God for help received; ask for grace where you need it.</p><a href="#learn" data-route="learn">Learn the framework <span aria-hidden="true">→</span></a></div>`;}
  function stepper(n){return `<nav class="steps" aria-label="Prayer steps">${['Your matter','Scripture','W.H.E.M.S.','Your prayer','Next step'].map((s,i)=>`<button type="button" data-step="${i+1}" ${n===i+1?'aria-current="step"':''}><span>${i+1}</span><b>${s}</b></button>`).join('')}</nav>`;}
  function controls(n,lastLabel='Continue'){return `<div class="flow-controls">${btn(n===1?'home':'back','← Back','quiet')}${btn('next',lastLabel+' <span aria-hidden="true">→</span>','primary')}</div>`;}
  function check(key,label,value){return `<label class="check"><input type="checkbox" data-field="${key}" ${value?'checked':''}><span>${label}</span></label>`;}
  function flow(n){
    if(!draft){route='home';return home();}
    const d=draft;
    let content='';
    if(n===1) content=title(d.mode==='thanks'?'Return with gratitude':'Begin with honesty',d.mode==='thanks'?'What are you thanking God for?':'What are you bringing to God?','A sentence is enough. You can change your wording later.')+field('topic','Your matter <span class="required">Required</span>',d.topic,'For example: how to respond to a difficult conversation',3,500)+field('context',d.mode==='thanks'?'What happened? <span class="optional">Optional</span>':'Why does this matter? <span class="optional">Optional</span>',d.context,'Only write details you are comfortable keeping on this device.')+`<p class="fine">Avoid names or identifying details you do not need to record.</p>`+controls(n);
    if(n===2) content=title('Scripture before the framework','What has God already made clear?','Read in context. These are your reflections, not a verdict made by the app.')+`<fieldset><legend>Choose what best describes your understanding <span class="optional">Optional</span></legend>${Object.entries(C.GATES).map(([k,v])=>`<label class="choice"><input type="radio" name="gate" data-field="gate" value="${k}" ${d.gate===k?'checked':''}><span>${esc(v[0])}</span></label>`).join('')}</fieldset>`+field('scripture','Passage and what it teaches <span class="optional">Optional</span>',d.scripture,'Note the reference, context and principle - not just a verse that supports your preference.')+`<div class="callout"><strong>Ask for wisdom, not a sign of approval.</strong><p>Scripture, wise counsel and relevant facts belong together. Personal calm is not proof that a choice is right.</p><div class="refs">${link(C.esv('James 1:5'),'James 1:5 · ESV')}${link(C.esv('Proverbs 15:22'),'Proverbs 15:22 · ESV')}${link('https://app.logos.com/','Open your Logos account')}</div><p class="fine">Logos opens separately. This app does not access your library.</p></div>`+controls(n,'Reflect');
    if(n===3){
      const a=C.AREAS.find(a=>a.key===area), r=d.areas[area], prior=journal.entries.find(e=>e.id===d.parentId);
      content=title('Give thanks. Ask for help.','Bring your whole self.','Use either invitation, both, or leave an area blank. These are prayer notes, not measures of faith.')+`<div class="area-nav" role="group" aria-label="Prayer areas">${C.AREAS.map(a=>`<button type="button" data-area="${a.key}" aria-pressed="${area===a.key}"><b>${a.key}</b><span>${a.name}</span></button>`).join('')}</div><section class="area-card"><div class="area-title"><span class="letter" aria-hidden="true">${a.key}</span><div><p class="eyebrow">${a.name}</p><h2>${a.question}</h2></div></div><p>${a.help}</p>${area==='S'?`<div class="foundation"><strong>Saved by grace, freed to serve God.</strong><p>Belonging to Christ is not earned by filling in these boxes. A struggle does not by itself mean you are unsaved.</p>${link(C.esv('Romans 6:17-23'),'Romans 6:17-23 · ESV')}<label class="field" for="belonging">How should the prayer express this?<select id="belonging" data-field="belonging"><option value="">No assumption about my faith</option><option value="trusting" ${d.belonging==='trusting'?'selected':''}>I am trusting Christ</option><option value="exploring" ${d.belonging==='exploring'?'selected':''}>I am exploring faith in Christ</option><option value="private" ${d.belonging==='private'?'selected':''}>Leave this personal</option></select></label></div>`:''}<div class="reflection-columns"><div class="reflection">${check('areas.'+area+'.thank','Thank God here',r.thank)}<div id="thank-fields" ${r.thank?'':'hidden'}>${field('areas.'+area+'.thankNote','Father, thank you for…',r.thankNote,area==='H'?'For example: helping me care about the other person':'Name the help or grace you recognise.')}</div></div><div class="reflection">${check('areas.'+area+'.ask','Ask for help here',r.ask)}<div id="ask-fields" ${r.ask?'':'hidden'}>${field('areas.'+area+'.askNote','Father, please help me…',r.askNote,area==='E'?'For example: respond gently while I am still hurt':'Name what remains difficult or uncertain.')}</div></div></div><details><summary>Scripture behind this invitation</summary><p><span class="tag">Passage summary</span> ${a.context}</p>${refs(a)}<p class="fine">The W.H.E.M.S. grouping is a teaching aid. Read the full passage before applying it.</p></details>${prior?`<details><summary>My earlier ${a.name.toLowerCase()} reflection</summary><p><strong>Thanksgiving:</strong> ${esc(prior.areas[area].thankNote||'No note recorded.')}</p><p><strong>Request:</strong> ${esc(prior.areas[area].askNote||'No note recorded.')}</p><p class="fine">Your earlier entry is preserved. Describe today in your own words.</p></details>`:''}</section><div class="flow-controls">${btn('previous-area',area==='W'?'← Scripture':'← Previous area','quiet')}${btn('next-area',area==='S'?'Shape my prayer →':'Next area →','primary')}</div><button type="button" class="quiet center" data-step="4">Pray with what I have written</button>`;
    }
    if(n===4){
      if(d.prayer===null)d.prayer=C.compose(d);
      content=title('Words to make your own','A prayer for this moment.','This draft uses your selections and words. Edit it freely. It is not a message from God.')+`<details class="fruit-panel"><summary>Ask for the Spirit’s fruit <span class="optional">Optional</span></summary><p>These describe how we respond, not whether a decision will succeed. The fruit overlaps all five areas.</p><div class="fruits">${C.FRUIT.map(f=>`<label class="check"><input type="checkbox" data-fruit="${f}" ${d.fruit.includes(f)?'checked':''}><span>${f}</span></label>`).join('')}</div>${link(C.esv('Galatians 5:22-25'),'All nine fruits · Galatians 5:22-25')}</details><div class="prayer-card">${field('prayer','My prayer',d.prayer,'Write your prayer here.',14,30000)}</div><p class="fine">After changing reflections or fruit, choose “Rebuild prayer” to update the draft. This replaces any edits.</p><div class="actions compact">${btn('regenerate','Rebuild prayer')}${btn('copy','Copy prayer')}${btn('download-html','Download HTML','secondary')}${btn('download','Download text','quiet')}</div>`+controls(n,'Next faithful step');
    }
    if(n===5){
      const g=C.guidance(d);
      content=title('Entrust the outcome to God','What is your next faithful step?','A small, responsible action is enough. This is your choice, not an instruction from the app.')+`<div class="callout"><span class="tag">Based on your Scripture reflection</span><h2>${esc(g.title)}</h2><p>${esc(g.body)}</p></div>`+field('nextStep','I will… <span class="optional">Optional</span>',d.nextStep,'For example: seek counsel, check a fact, apologise, or fulfil a clear responsibility.')+`<label class="field" for="revisit">Revisit on <span class="optional">Optional - no reminder is scheduled</span><input id="revisit" type="date" data-field="revisit" value="${esc(d.revisit)}"></label><div class="save-note"><strong>Save in this browser only</strong><p>Save opens a new tab with your prayer and a Download HTML button. Downloading creates a separate file you can keep.</p><p>Your words are not sent to an AI or stored in a cloud journal. This browser’s storage is not encrypted by the app. Anyone using the same browser profile may read it; clearing site data can remove it.</p><p class="fine">The website host still receives ordinary page requests. A preview URL and the production URL keep separate journals.</p></div><div class="flow-controls">${btn('back','← Prayer','quiet')}${btn('save','Save & open download','primary')}</div><div class="actions compact">${btn('download-html','Download HTML','secondary')}${btn('download','Download text','quiet')}${btn('home','Finish without saving','quiet')}</div>`;
    }
    return `<div class="flow">${stepper(n)}${content}</div>`;
  }
  function journalView(){
    refresh();let legacy=null;try{legacy=storage.getItem(C.LEGACY);}catch{}
    return title('Keep a small record','Your prayer journal.','Only entries saved in this browser appear here. Give thanks without pretending that every struggle has disappeared.')+`<div class="actions compact">${btn('new','New prayer','primary')}${btn('thanks','Give thanks')}${btn('backup','Download backup','quiet')}</div>${legacy&&!journal.entries.some(e=>e.id==='legacy-v1')?`<div class="callout"><h2>An earlier prayer was found</h2><p>You can copy it into this journal. The original saved data will be left untouched.</p>${btn('migrate','Import earlier prayer')}</div>`:''}${!journal.ok?`<div class="callout"><p>${esc(journal.error)}</p>${btn('raw-backup','Download existing raw data')}</div>`:''}${journal.entries.length?`<div class="entries">${journal.entries.map(d=>`<article class="entry"><div class="entry-meta"><span class="tag">${d.parentId?'Return to prayer':d.mode==='thanks'?'Thanksgiving':'Seeking help'}</span><span>${esc(date(d.updatedAt))}</span></div><h2>${esc(d.topic)}</h2><p>${esc(d.nextStep||'No next step recorded.')}</p><div class="actions compact">${btn('open','Read prayer','secondary',`data-id="${d.id}"`)}${btn('review','Return & give thanks','quiet',`data-id="${d.id}"`)}</div></article>`).join('')}</div>`:`<div class="empty"><p class="eyebrow">Room to begin</p><h2>No saved prayers yet.</h2><p>You can give thanks now, even without an earlier entry.</p></div>`}`;
  }
  function entryView(id){
    const d=journal.entries.find(e=>e.id===id);if(!d)return title('Journal','Prayer not found.','It may have been removed from this browser.')+btn('journal','Return to journal');
    return title(d.mode==='thanks'?'Thanksgiving':'A saved prayer',esc(d.topic),esc(date(d.updatedAt)))+`<article class="prayer-card read-prayer">${esc(d.prayer??C.compose(d))}</article><div class="record-summary"><h2>What I brought to God</h2>${C.AREAS.map(a=>`<p><b>${a.key} · ${a.name}</b><span>${status(d.areas[a.key])}</span></p>`).join('')}</div>${d.scripture?`<div class="callout"><h2>My Scripture reflection</h2><p class="pre">${esc(d.scripture)}</p></div>`:''}${d.nextStep?`<div class="callout"><h2>My next faithful step</h2><p class="pre">${esc(d.nextStep)}</p></div>`:''}${d.revisit?`<p>Revisit: ${esc(d.revisit)}. No reminder scheduled.</p>`:''}${d.legacyNote?`<details><summary>Earlier thanksgiving note</summary><p class="pre">${esc(d.legacyNote)}</p></details>`:''}<div class="actions">${btn('review','Return & give thanks','primary',`data-id="${d.id}"`)}${btn('edit','Edit this entry','secondary',`data-id="${d.id}"`)}${btn('open-download','Open download page (new tab)','secondary',`data-id="${d.id}"`)}${btn('download-html','Download HTML','secondary',`data-id="${d.id}"`)}${btn('download','Download text','quiet',`data-id="${d.id}"`)}${btn('delete','Delete entry','quiet',`data-id="${d.id}"`)}</div>`;
  }
  function downloadView(id){
    refresh();
    const d=journal.entries.find(e=>e.id===id);
    if(!d)return title('Download','Prayer not available here.','This page reads the journal in this browser and on this website address. It is not a public sharing link. The entry may have been removed, or browser storage may be unavailable.')+btn('journal','Return to journal');
    return `<section class="download-tools">${title('Saved in this browser','Your prayer is ready to download.','Save keeps a journal entry here. Download HTML creates a separate, readable file for you to keep.')}<div class="actions">${btn('download-html','Download HTML','primary',`data-id="${d.id}"`)}${btn('print','Print','secondary')}${btn('open','Back to saved entry','quiet',`data-id="${d.id}"`)}</div><p class="fine">File: <strong>${esc(X.filename(d))}</strong><br>Your browser chooses where to save it. Check its Downloads list or the Files app. Keep the file private.</p><p class="fine">The copy opens without this website. Scripture and study links need internet access. This tab’s address is not a shareable copy of your prayer.</p></section>`+X.article(d,'h2');
  }
  function openDownload(id){
    // Called synchronously by a button click, after the local save is verified.
    // Open a blank tab first, sever its opener, then navigate to a fixed same-origin route.
    // No personal text is placed in a URL, and no upload is performed.
    let tab=null;
    try{
      const url=new URL(location.href);url.search='';url.hash='download-'+id;
      tab=window.open('','_blank');
      if(!tab)return false;
      tab.opener=null;
      tab.location.replace(url.href);
      return true;
    }catch{try{if(tab)tab.close();}catch{}return false;}
  }
  function learn(){return title('A five-minute introduction','One prayer can hold both.','Thank God for where he has helped. Ask him for help where you are still struggling.')+`<div class="callout"><h2>Not a five-out-of-five test</h2><p>Three areas of thanksgiving do not cancel two areas needing attention. Nor must every uncomfortable feeling disappear before you do what is right.</p>${link(C.esv('Matthew 26:37-39'),'Jesus prays through sorrow · ESV')}</div><div class="learn-list">${C.AREAS.map(a=>`<details><summary><span class="small-letter">${a.key}</span> ${a.name} · ${a.question}</summary><p>${a.help}</p><p><span class="tag">Passage summary</span> ${a.context}</p>${refs(a)}</details>`).join('')}</div><section class="callout"><h2>“Thank you” and “help me” belong together.</h2><p>For example: “Father, thank you for helping me know what is right and become willing to listen. I am still hurt and want to prove myself. Please correct my motives and help me answer gently.”</p>${link(C.esv('Philippians 4:6-7'),'Philippians 4:6-7 · ESV')}</section><section class="callout"><h2>Fruit, not a forecast</h2><p>${C.FRUIT.join(' · ')}.</p><p>Ask the Holy Spirit to form these qualities as you decide and act. No fruit belongs exclusively to one W.H.E.M.S. area.</p>${link(C.esv('Galatians 5:22-25'),'Galatians 5:22-25 · ESV')}</section><section class="callout"><h2>Soul: belonging, not performance</h2><p>Jesus frees from slavery to sin. Salvation is by grace through faith, not by completing a prayer exercise. The app never classifies a person as saved or unsaved.</p><div class="refs">${link(C.esv('John 8:34-36'),'John 8:34-36 · ESV')}${link(C.esv('Ephesians 2:8-10'),'Ephesians 2:8-10 · ESV')}</div><p>Heart, mind, will, emotions and soul overlap in biblical usage. W.H.E.M.S. is a prayer aid, not five separate compartments of a person.</p></section>${btn('new','Begin a prayer','primary')}`;}
  function privacy(){return title('Your words. Your choice.','Privacy & sources.','Simple by design, with clear limits.')+`<section class="callout"><h2>What stays in your browser</h2><p>No sign-in, analytics script, AI request or cloud journal is included. A prayer is stored only when you press Save. Unsaved work is lost on reload or closing the tab.</p><p>Local saving is not encryption or a backup. Browser settings, storage limits or clearing data can remove prayers. Use Download HTML, Download text or Download backup for a personal copy, and keep that copy private.</p><p>The hosting service receives ordinary requests to load the site. External study sites receive a visit only when you open a link; Wholehearted does not include your reflections in those links. Their own privacy policies apply.</p></section><section class="callout"><h2>Our source boundaries</h2><p><strong>ESV.org</strong> is the Scripture reading destination. The explanations here are short passage summaries and applications, not verbatim ESV quotations.</p><p><strong>STEP Bible and Blue Letter Bible</strong> open the relevant passage for word study and context. Links do not mean the app has fetched or verified live lexical data.</p><p><strong>Logos</strong> opens your own account in a separate tab. Your owned library is not connected, searched or imported by this app.</p><div class="refs">${link('https://www.esv.org/','ESV.org')}${link('https://www.stepbible.org/','STEPBible.org')}${link('https://www.blueletterbible.org/','Blue Letter Bible')}${link('https://app.logos.com/','Logos account')}</div><p>Scripture governs the framework, not the other way round. W.H.E.M.S. and its prayer templates are teaching applications, not biblical commands.</p></section><section class="callout"><h2>Aids have limits</h2><p>This app does not decide God’s will, assess salvation or diagnose emotions. Prayer does not replace responsible action, pastoral care or appropriate professional help.</p><p>Revisit dates are notes for you. There are no automatic reminders. External study links need an internet connection.</p></section>`;}
  function render(){
    notify('');
    const match=/^flow-([1-5])$/.exec(route);
    main.innerHTML=match?flow(+match[1]):route==='journal'?journalView():route==='learn'?learn():route==='privacy'?privacy():route.startsWith('entry-')?entryView(route.slice(6)):route.startsWith('download-')?downloadView(route.slice(9)):home();
    document.querySelectorAll('.header nav a').forEach(a=>{if(a.dataset.route===route)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    document.title=(route.startsWith('download-')?'Download prayer · ':match?'Prayer · ':'')+'Wholehearted · W.H.E.M.S. Prayer';focus();
  }
  function start(mode,prior){
    if(dirty&&!confirm('Replace this unsaved prayer? Saved journal entries will not be changed.'))return;
    draft=prior?C.review(prior):C.blank(mode);area='W';dirty=true;go('flow-1');
  }
  function navigateStep(n){
    if(!draft)return go('home');
    if(n>1&&!draft.topic.trim()){go('flow-1');notify('Please name the matter first.');document.getElementById('f-topic').focus();return;}
    go('flow-'+Math.min(5,Math.max(1,n)));
  }
  function download(data,name,type='text/plain;charset=utf-8'){
    const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.hidden=true;document.body.append(a);try{a.click();}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);}notify('Download prepared. Check your browser’s Downloads list or Files app. Keep personal prayer files private.');
  }
  document.addEventListener('input',event=>{
    const el=event.target, key=el.dataset.field;if(!key||!draft)return;
    const value=el.type==='checkbox'?el.checked:el.value;
    const parts=key.split('.');
    if(parts.length===3&&parts[0]==='areas'&&C.KEYS.includes(parts[1])&&['thank','ask','thankNote','askNote'].includes(parts[2])){
      draft.areas[parts[1]][parts[2]]=value;
      if(['thank','ask'].includes(parts[2])){const panel=document.getElementById(parts[2]+'-fields');if(panel)panel.hidden=!value;}
    }else if(['topic','context','gate','scripture','belonging','prayer','nextStep','revisit'].includes(key))draft[key]=value;
    dirty=true;
  });
  document.addEventListener('change',event=>{
    const fruit=event.target.dataset.fruit;if(!draft||!C.FRUIT.includes(fruit))return;
    draft.fruit=event.target.checked?[...new Set([...draft.fruit,fruit])]:draft.fruit.filter(f=>f!==fruit);dirty=true;
    notify('Fruit selection updated. Choose Rebuild prayer to include it in your words.');
  });
  document.addEventListener('click',async event=>{
    if(event.target.closest('.skip')){event.preventDefault();main.focus();return;}
    const el=event.target.closest('[data-route],[data-action],[data-step],[data-area]');if(!el)return;
    if(el.dataset.route){event.preventDefault();return go(el.dataset.route);}
    if(el.dataset.step)return navigateStep(+el.dataset.step);
    if(el.dataset.area){area=el.dataset.area;return render();}
    const action=el.dataset.action, id=el.dataset.id, saved=journal.entries.find(e=>e.id===id), n=Number(route.split('-')[1]);
    try {
      if(action==='new'||action==='thanks')return start(action==='new'?'seek':'thanks');
      if(['home','journal'].includes(action))return go(action);
      if(action==='resume')return navigateStep(1);
      if(action==='next')return navigateStep(n+1);
      if(action==='back')return navigateStep(n-1);
      if(action==='previous-area'){const i=C.KEYS.indexOf(area);if(i===0)return navigateStep(2);area=C.KEYS[i-1];return render();}
      if(action==='next-area'){const i=C.KEYS.indexOf(area);if(i===4)return navigateStep(4);area=C.KEYS[i+1];return render();}
      if(action==='regenerate'){if(!confirm('Rebuild from your current reflections and fruit? This will replace edits in the prayer box.'))return;draft.prayer=C.compose(draft);dirty=true;render();return notify('Prayer rebuilt from your current reflections.');}
      if(action==='copy'){try{await navigator.clipboard.writeText(draft.prayer??C.compose(draft));notify('Prayer copied.');}catch{document.getElementById('f-prayer')?.select();notify('Automatic copy is unavailable. Your prayer is selected; use your device’s Copy command.');}return;}
      if(action==='download-html'){
        const d=saved||draft;
        if(!d)return notify('No prayer is available to download.');
        return download(X.html(d),X.filename(d),'text/html;charset=utf-8');
      }
      if(action==='open-download'&&saved){
        const opened=openDownload(saved.id);
        return notify(opened?'Download page opened in a new tab.':'Your browser blocked the new tab. Use Download HTML here, or allow pop-ups for this site.');
      }
      if(action==='print')return window.print();
      if(action==='download')return download(C.exportText(saved||draft),'wholehearted-prayer.txt');
      if(action==='backup'){if(!journal.ok)return notify('Existing data could not be read. Use Download existing raw data instead of an empty backup.');return download(JSON.stringify({version:C.VERSION,entries:journal.entries},null,2),'wholehearted-journal.json','application/json');}
      if(action==='raw-backup')return download(storage.getItem(C.STORAGE)||'','wholehearted-existing-data.json','application/json');
      if(action==='save'){
        if(!journal.ok)return notify(journal.error);
        if(draft.prayer===null)draft.prayer=C.compose(draft);
        if(!draft.prayer.trim())return notify('Your prayer is empty. Return to the prayer step to write or rebuild it.');
        const result=C.write(storage,C.upsert(journal.entries,draft),journal.raw);
        if(!result.ok)return notify(result.error);
        journal=result;dirty=false;const savedId=draft.id;draft=null;const opened=openDownload(savedId);go('entry-'+savedId);return notify(opened?'Saved in this browser. A new tab has your prayer and Download HTML button. No cloud copy was created.':'Saved in this browser, but the new tab was blocked. Use Download HTML below. No cloud copy was created.');
      }
      if(action==='migrate'){
        if(!journal.ok)return notify(journal.error);
        const imported=C.migrate(storage.getItem(C.LEGACY));
        const result=C.write(storage,C.upsert(journal.entries,imported),journal.raw);
        if(!result.ok)return notify(result.error);journal=result;render();return notify('Earlier prayer copied. Its original data remains untouched.');
      }
      if(action==='open')return go('entry-'+id);
      if(action==='review'&&saved)return start('thanks',saved);
      if(action==='edit'&&saved){if(dirty&&!confirm('Replace the unsaved form with this entry?'))return;draft=C.copy(saved);dirty=false;area='W';return navigateStep(1);}
      if(action==='delete'&&saved){if(!confirm('Delete this saved entry from this browser? Download a copy first if you need it.'))return;const result=C.write(storage,journal.entries.filter(e=>e.id!==id),journal.raw);if(!result.ok)return notify(result.error);journal=result;go('journal');return notify('Entry deleted from this browser.');}
    }catch{notify('That action could not be completed. Your existing saved data has not intentionally been changed. Download your current prayer before reloading.');}
  });
  window.addEventListener('popstate',()=>{route=location.hash.slice(1)||'home';render();});
  window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
  window.addEventListener('storage',e=>{if(e.key===C.STORAGE)notify('The journal changed in another tab. Download any unsaved prayer, then reload before saving.');});
  route=location.hash.slice(1)||'home';render();if(!journal.ok)notify(journal.error);
})();
