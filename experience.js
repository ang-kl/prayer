/* Viewport-aware navigation and field-level guidance. No journal access or network calls. */
(function(root){
  'use strict';
  function metrics(v){
    const width=Math.max(1,Number(v.width)||1),height=Math.max(1,Number(v.height)||1);
    const top=Math.max(0,Number(v.top)||0),left=Math.max(0,Number(v.left)||0);
    return {width,height,top,left,bottom:Math.max(0,(Number(v.layoutHeight)||height)-height-top),
      right:Math.max(0,(Number(v.layoutWidth)||width)-width-left),
      compact:width<700||height<520,
      keyboard:!!v.editing&&(Number(v.scale)||1)<1.1&&Math.max((Number(v.layoutHeight)||height)-height,(Number(v.expandedHeight)||height)-height)>130};
  }
  if(typeof module==='object'&&module.exports){module.exports={metrics};return;}
  const doc=root.document;
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let host=null,dock=null,notice=null,pending=null,frame=0,serial=0,lastReturn=null,lastGeometry=null;
  const expanded=new Map();
  const $=s=>doc.querySelector(s);
  const editable=e=>!!e?.matches('textarea,input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]),[contenteditable=true]');
  function view(){
    const v=root.visualViewport,w=v?.width||root.innerWidth,h=v?.height||root.innerHeight;
    const key=Math.round(root.innerWidth),editing=editable(doc.activeElement);
    if(!editing)expanded.set(key,Math.max(expanded.get(key)||0,h));
    return metrics({width:w,height:h,top:v?.offsetTop,left:v?.offsetLeft,layoutWidth:root.innerWidth,layoutHeight:root.innerHeight,scale:v?.scale,editing,expandedHeight:expanded.get(key)});
  }
  function inViewport(e){const v=view(),r=e.getBoundingClientRect();return r.bottom>v.top&&r.top<v.top+v.height;}
  function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;layout();});}
  function layout(){
    const v=view(),html=doc.documentElement;
    const geometry=[v.width,v.height,root.innerWidth,root.innerHeight].join(':');
    const resized=lastGeometry!==null&&geometry!==lastGeometry;lastGeometry=geometry;
    for(const [name,value] of Object.entries({'vp-height':v.height,'vp-width':v.width,'vp-top':v.top,'vp-left':v.left,'vp-bottom':v.bottom,'vp-right':v.right}))html.style.setProperty('--'+name,value+'px');
    html.dataset.compactControls=String(v.compact);html.dataset.keyboard=String(v.keyboard);
    html.dataset.layoutOrientation=root.innerWidth>root.innerHeight?'landscape':'portrait';
    if(!dock)return;
    dock.hidden=!!$('#reader')?.open;
    if(!dock.hidden)html.style.setProperty('--tools-height',dock.getBoundingClientRect().height+'px');
    const extent=Math.max(0,doc.documentElement.scrollHeight-root.innerHeight);
    dock.querySelector('[data-fab=up]').disabled=root.scrollY<2;
    dock.querySelector('[data-fab=down]').disabled=root.scrollY>=extent-2;
    const top=v.top+20;
    let current=null;for(const e of doc.querySelectorAll('#main [data-toc-label]'))if(e.getBoundingClientRect().top<=top)current=e;
    dock.dataset.current=current?.id||'main';
    if(v.keyboard||resized)requestAnimationFrame(()=>avoidOverlap(doc.activeElement));
  }
  function visibleBounds(target){
    const v=view();let top=v.top+20,bottom=v.top+v.height-20;
    const r=target.getBoundingClientRect();
    for(const el of [dock,notice]){
      if(!el||el.hidden||!inViewport(el))continue;
      const o=el.getBoundingClientRect();
      if(r.right>o.left&&r.left<o.right){if(el===notice)top=Math.max(top,o.bottom+16);else bottom=Math.min(bottom,o.top-16);}
    }
    // There is no sticky masthead. A user can always reveal focused content above the dock.
    return {top,bottom:Math.max(top+60,bottom)};
  }
  function avoidOverlap(target){
    if(!target?.isConnected||target.closest('dialog,#page-tools,#notice')||!$('#main')?.contains(target))return;
    const r=target.getBoundingClientRect(),b=visibleBounds(target);
    let by=0;
    if(r.top<b.top)by=r.top-b.top;
    else if(r.bottom>b.bottom)by=r.height>b.bottom-b.top?r.top-b.top:r.bottom-b.bottom;
    if(Math.abs(by)>2)root.scrollBy({top:by,behavior:'instant'});
  }
  function reveal(selector,{focus=true}={}){
    const target=typeof selector==='string'?$(selector):selector;
    if(!target)return false;
    if($('#reader')?.open)host.closeReader();
    for(let el=target.parentElement;el;el=el.parentElement)if(el.tagName==='DETAILS')el.open=true;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      if(!target.isConnected)return;
      if(focus){if(!target.matches('input,textarea,select,button,a,[tabindex]'))target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}
      const r=target.getBoundingClientRect(),bounds=visibleBounds(target);
      root.scrollBy({top:r.top-bounds.top-12,behavior:'instant'});
      requestAnimationFrame(()=>avoidOverlap(target));
    }));
    return true;
  }
  function notify(text,actions='',kind='status'){
    if(!notice)return;
    notice.replaceChildren();notice.hidden=!text;if(!text)return;
    notice.dataset.kind=kind;
    const heading=doc.createElement('strong');heading.className='notice-title';heading.textContent=kind==='error'?'Something needs attention':'Wholehearted';
    const p=doc.createElement('p');p.textContent=text;
    const close=doc.createElement('button');close.type='button';close.className='notice-dismiss';close.textContent='Dismiss';close.setAttribute('aria-label','Dismiss status message');close.addEventListener('click',()=>{notice.hidden=true;});
    notice.append(heading,p,close);
    if(actions){const box=doc.createElement('div');box.className='actions';box.innerHTML=actions;notice.append(box);}
    // A modal reader makes the rest of the page inert. Put reader feedback inside it as well.
    if($('#reader')?.open){const old=$('#reader-notice');old?.remove();const local=doc.createElement('div');local.id='reader-notice';local.className='inline-status';local.setAttribute('role','status');local.textContent=text;$('#reader-content')?.prepend(local);}
    schedule();
  }
  function targetReady(error){const el=$(error.selector);return !!el&&(error.check==='checked'?el.checked:!!el.value?.trim());}
  function controlID(e){if(!e.id)e.id='wholehearted-control-'+(++serial);return e.id;}
  function cleanErrors(){
    for(const e of doc.querySelectorAll('[data-attention-mark]')){
      e.removeAttribute('aria-invalid');const id=e.dataset.attentionMark;
      const refs=(e.getAttribute('aria-describedby')||'').split(/\s+/).filter(x=>x&&x!==id);
      if(refs.length)e.setAttribute('aria-describedby',refs.join(' '));else e.removeAttribute('aria-describedby');
      delete e.dataset.attentionMark;
    }
    doc.querySelectorAll('.needs-attention').forEach(e=>e.classList.remove('needs-attention'));
    doc.querySelectorAll('.field-action-note,.action-feedback').forEach(e=>e.remove());
  }
  function returnMarkup(){return `<button type="button" data-return-origin>Return to ${escape(pending.originLabel)}</button>`;}
  function updateErrors(){
    if(!pending)return;
    const remaining=pending.errors.filter(e=>!targetReady(e));
    for(const error of pending.errors){
      const target=$(error.selector),note=$('#'+error.noteID);if(!target||!note)continue;
      const ready=targetReady(error),group=target.closest('[data-attention-group],label.field,label.check')||target.parentElement;
      if(ready){target.removeAttribute('aria-invalid');group.classList.remove('needs-attention');}
      else{target.setAttribute('aria-invalid','true');group.classList.add('needs-attention');}
      note.classList.toggle('resolved',ready);
      note.innerHTML=`<strong>${ready?'This step is complete.':'Your action is needed.'}</strong><p>${escape(ready?'Your choice has been recorded. No AI request has been sent automatically.':error.message)}</p>`+
        (ready&&remaining.length?`<button type="button" data-locate="${escape(remaining[0].selector)}">Next: ${escape(remaining[0].label)}</button>`:returnMarkup());
    }
    const summary=pending.summary;
    if(summary?.isConnected){summary.classList.toggle('resolved',!remaining.length);summary.innerHTML=remaining.length?
      `<h3>Before we continue</h3><p>${remaining.length===1?'One step needs':'These steps need'} your attention. Your writing is safe.</p><ul>${remaining.map(e=>`<li><button type="button" data-locate="${escape(e.selector)}">${escape(e.label)}</button><span>${escape(e.message)}</span></li>`).join('')}</ul>`:
      `<h3>Ready when you are</h3><p>The missing steps are complete. Nothing will be sent until you choose the AI action again.</p>${returnMarkup()}`;}
    schedule();
  }
  function requireActions(errors,origin,originLabel){
    cleanErrors();notice.hidden=true;
    if(!errors.length){pending=null;return false;}
    const start=typeof origin==='string'?$(origin):origin;
    const summary=doc.createElement('div');summary.className='action-feedback';summary.setAttribute('role','alert');
    summary.setAttribute('aria-atomic','true');summary.id='action-feedback';
    const actionRow=start?.closest('.actions')||start;actionRow?.after(summary);
    pending={errors:errors.map(e=>({...e})),summary,origin:start,originLabel:originLabel||'the AI action'};
    lastReturn=start;
    for(const error of pending.errors){
      const target=$(error.selector);if(!target)continue;
      error.noteID=controlID(target)+'-action-note';
      const group=target.closest('[data-attention-group],label.field,label.check')||target.parentElement;
      const note=doc.createElement('div');note.className='field-action-note';note.id=error.noteID;
      group.after(note);
      target.dataset.attentionMark=error.noteID;
      const prev=target.getAttribute('aria-describedby')||'';target.setAttribute('aria-describedby',(prev+' '+error.noteID).trim());
    }
    updateErrors();reveal(errors[0].selector);return true;
  }
  function decorate(){
    const main=$('#main');if(!main)return;
    // Only fixed navigation labels are used - never prior journal titles or private excerpts.
    if(!main.querySelector('[data-toc-label]')){
      const plans=[['.workspace .writing-paper','journal-write','Write a prayer'],['.notes-column','journal-reflect','W.H.E.M.S. reflections'],['.catalogue-tools','scripture-search','Find a passage'],['#catalogue-results','scripture-list','Scripture references'],['.filters','journal-filter','Find an entry'],['#index-results','journal-index','Browse entries'],['.reading-page','saved-reading','Read this entry'],['.export-sheet','download-reading','Prayer reading copy']];
      for(const [selector,id,label] of plans){const e=main.querySelector(selector);if(e){e.id=e.id||id;e.dataset.tocLabel=label;}}
    }
  }
  function contents(){
    decorate();const links=[{id:'main',label:'Start of this page'},...[...doc.querySelectorAll('#main [data-toc-label]')].map(e=>({id:e.id,label:e.dataset.tocLabel})),{id:'page-end',label:'End of this page'}];
    const current=dock?.dataset.current;
    host.panel('Contents',`<nav class="page-contents" aria-label="Contents of this page"><p>Choose where to continue. Your words stay in place.</p>${links.map(e=>`<button type="button" data-locate="#${escape(e.id)}" ${current===e.id?'aria-current="location"':''}>${escape(e.label)}${current===e.id?'<span>Current section</span>':''}</button>`).join('')}</nav>`);
  }
  function refresh(){
    if(!host)return;
    cleanErrors();pending=null;decorate();layout();
  }
  function init(h){
    if(host)return;host=h;notice=$('#notice');notice.setAttribute('aria-atomic','true');
    dock=doc.createElement('nav');dock.id='page-tools';dock.className='page-tools';dock.setAttribute('aria-label','Page navigation');
    dock.innerHTML='<button type="button" data-fab="contents" aria-label="Open table of contents" aria-haspopup="dialog"><span aria-hidden="true">☰</span><span>Contents</span></button><button type="button" data-fab="up" aria-label="Scroll up one screen" title="Scroll up one screen"><span aria-hidden="true">↑</span><span>Up</span></button><button type="button" data-fab="down" aria-label="Scroll down one screen" title="Scroll down one screen"><span aria-hidden="true">↓</span><span>Down</span></button>';
    doc.body.append(dock);
    const footer=$('.site-footer');if(footer)footer.id='page-end';
    doc.addEventListener('click',e=>{
      const fab=e.target.closest('[data-fab]');if(fab){if(fab.dataset.fab==='contents')return contents();const distance=Math.max(100,view().height-140);root.scrollBy({top:(fab.dataset.fab==='up'?-1:1)*distance,behavior:root.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});return;}
      const jump=e.target.closest('[data-locate]');if(jump){e.preventDefault();reveal(jump.dataset.locate);return;}
      if(e.target.closest('[data-return-origin]')){reveal(pending?.origin?.isConnected?pending.origin:lastReturn?.isConnected?lastReturn:'#guide-prayers');}
    });
    for(const type of ['input','change'])doc.addEventListener(type,()=>{requestAnimationFrame(updateErrors);});
    doc.addEventListener('focusin',e=>{schedule();setTimeout(()=>avoidOverlap(e.target),120);});
    doc.addEventListener('focusout',schedule);
    root.addEventListener('scroll',schedule,{passive:true});root.addEventListener('resize',schedule,{passive:true});
    root.visualViewport?.addEventListener('resize',schedule,{passive:true});root.visualViewport?.addEventListener('scroll',schedule,{passive:true});
    root.screen?.orientation?.addEventListener('change',schedule);
    new MutationObserver(schedule).observe($('#reader'),{attributes:true,attributeFilter:['open']});
    new ResizeObserver(schedule).observe(doc.body);
    layout();
  }
  root.WholeheartedExperience={metrics,init,refresh,notify,requireActions,reveal,layout};
})(globalThis);
