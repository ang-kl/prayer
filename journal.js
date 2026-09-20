/* Versioned local journal adapter. Display build identity is unrelated to data schema.
   v2/v1 originals are never removed. Migration is in memory until an explicit Save. */
(function(root){'use strict';
const C=typeof module==='object'&&module.exports?require('./core.js'):root.WholeheartedCore;
const G=typeof module==='object'&&module.exports?require('./guidance-core.js'):root.WholeheartedGuidance;
const STORAGE='wholehearted-journal-v3',VERSION=3,MAX=100;
const TYPES=['request','thanksgiving','mixed'],FORMS=['sentence','whems','personal'];
const STATUSES={'':'Not recorded',waiting:'Waiting',partly:'Partly answered',answered:'Answered as requested',differently:'Answered differently',clearer:'Direction became clearer',changed:'Circumstances changed',unresolved:'No clear answer yet',closed:'Closed / no longer applicable'};
const txt=(v,n=2000)=>typeof v==='string'?v.slice(0,n):'';
const obj=x=>x&&typeof x==='object'&&!Array.isArray(x);
const validDate=s=>typeof s==='string'&&s.length<=40&&!Number.isNaN(new Date(s).getTime());
function tags(v){return [...new Set((Array.isArray(v)?v:String(v||'').split(/[\s,]+/)).map(x=>String(x).replace(/^#+/,'').toLowerCase().replace(/[^\p{L}\p{N}_-]/gu,'').slice(0,32)).filter(Boolean))].slice(0,12);}
function blank(type='request',now=new Date().toISOString(),id){const d=C.blank(type==='thanksgiving'?'thanks':'seek',now,id);return {...d,entryType:TYPES.includes(type)?type:'request',form:'sentence',prayer:'',tags:[],prayedAt:now,advice:'',answerStatus:'',answerNote:'',referenceIds:[],revisions:[],journey:G.state(),prayerForms:G.forms()};}
function normalise(raw){
 const d=C.normalise(raw);
 d.entryType=TYPES.includes(raw.entryType)?raw.entryType:d.mode==='thanks'?'thanksgiving':'request';d.mode=d.entryType==='thanksgiving'?'thanks':'seek';
 d.form=FORMS.includes(raw.form)?raw.form:'whems';d.tags=tags(raw.tags||[]);d.prayedAt=validDate(raw.prayedAt)?raw.prayedAt:validDate(d.createdAt)?d.createdAt:'';
 d.advice=txt(raw.advice);d.answerNote=txt(raw.answerNote);d.answerStatus=Object.hasOwn(STATUSES,raw.answerStatus)?raw.answerStatus:'';
 d.referenceIds=Array.isArray(raw.referenceIds)?[...new Set(raw.referenceIds.filter(s=>typeof s==='string'&&/^[a-z0-9-]{1,80}$/.test(s)))].slice(0,40):[];
 d.journey=G.state(raw.journey);d.prayerForms=G.forms(raw.prayerForms);
 if(raw.revisions!==undefined&&!Array.isArray(raw.revisions))throw Error('Unrecognised revision history.');
 if((raw.revisions||[]).length>25)throw Error('This entry has reached its revision limit. Create a linked follow-up instead.');
 d.revisions=(raw.revisions||[]).map(r=>{if(!obj(r)||!obj(r.record)||!validDate(r.at))throw Error('Unrecognised revision history.');return {at:r.at,record:normalise({...r.record,revisions:[]})};});
 return d;
}
function decode(raw){if(raw===null)return [];if(typeof raw!=='string'||raw.length>5000000)throw Error('Saved data is too large or invalid.');const d=JSON.parse(raw);if(!obj(d)||d.version!==VERSION||!Array.isArray(d.entries)||d.entries.length>MAX)throw Error('Unrecognised journal format.');const entries=d.entries.map(normalise);if(new Set(entries.map(x=>x.id)).size!==entries.length)throw Error('Duplicate prayer identifiers.');return entries;}
function read(storage){
 try{const raw=storage.getItem(STORAGE);if(raw!==null)return {ok:true,raw,legacyRaw:null,entries:decode(raw),source:'v3',error:''};const legacyRaw=storage.getItem(C.STORAGE);return {ok:true,raw:null,legacyRaw,entries:C.decode(legacyRaw).map(normalise),source:legacyRaw===null?'empty':'v2',error:''};}
 catch{return {ok:false,raw:null,legacyRaw:null,entries:[],source:'unreadable',error:'Your saved journal could not be read. It has not been replaced. Download your current words and keep the existing data before trying again.'};}
}
function write(storage,entries,expected){
 try{if(!expected.ok)return {ok:false,error:expected.error};
 if(storage.getItem(STORAGE)!==expected.raw||(expected.raw===null&&storage.getItem(C.STORAGE)!==expected.legacyRaw))return {ok:false,error:'Your journal changed in another tab. Download unsaved words, then reload before saving.'};
 const raw=JSON.stringify({version:VERSION,entries:entries.map(normalise)});decode(raw);storage.setItem(STORAGE,raw);if(storage.getItem(STORAGE)!==raw)return {ok:false,error:'The save could not be verified. Download a copy before leaving.'};
 return {ok:true,raw,legacyRaw:null,entries:decode(raw),source:'v3',error:''};
 }catch{return {ok:false,error:'Not saved: browser storage is unavailable or full. Your words are still on screen. Download a copy.'};}
}
function upsert(entries,raw,now=new Date().toISOString()){
 const d=normalise(raw);if(!d.prayer?.trim())throw Error('Write a prayer, or choose Shape my prayer, before saving.');
 const prior=entries.find(x=>x.id===d.id),next=entries.filter(x=>x.id!==d.id);
 if(next.length>=MAX)throw Error('The journal is full (100 entries). Download a backup and remove an older entry, or download this prayer without saving.');
 if(prior){d.createdAt=prior.createdAt;d.revisions=C.copy(prior.revisions||[]);const previous=normalise({...prior,revisions:[]});const compare=x=>JSON.stringify({...x,revisions:[],updatedAt:''});if(compare(previous)!==compare(d)){if(d.revisions.length>=25)throw Error('This entry has 25 revisions. Create a linked follow-up to preserve its history.');d.revisions.push({at:now,record:previous});}}
 d.updatedAt=now;return [d,...next];
}
function follow(prior,type='thanksgiving',now,id){const d=blank(type,now,id);d.topic=prior.topic;d.parentId=prior.id;if(prior.journey?.issue)d.journey.issue=prior.journey.issue;return d;}
function compose(d){
 if(d.form==='personal')return d.prayer||'';
 if(d.form==='whems')return C.compose({...d,topic:d.topic.trim()||'what I am bringing before you',mode:d.entryType==='thanksgiving'?'thanks':'seek'});
 const thanks=C.AREAS.filter(a=>d.areas[a.key].thank).map(a=>d.areas[a.key].thankNote.trim()||a.thank);
 const asks=C.AREAS.filter(a=>d.areas[a.key].ask).map(a=>d.areas[a.key].askNote.trim()||a.ask);
 const t=thanks.length?'thank you for '+thanks.join('; '):'I bring '+(d.topic.trim()||'this matter')+' before you';
 const a=asks.length?'; please help me with '+asks.join('; '):'; guide my response by your Word';
 return 'Father, '+t+a+', so that my decision and response honour Christ.';
}
function meaningful(d){return !!(d.journey?.issue?.trim()||d.prayerForms?.sentence?.trim()||d.prayerForms?.whems?.trim()||d.prayerForms?.extended?.trim()||d.topic.trim()||d.prayer?.trim()||d.context.trim()||d.scripture.trim()||d.advice.trim()||d.nextStep.trim()||d.answerNote.trim()||C.KEYS.some(k=>d.areas[k].thank||d.areas[k].ask||d.areas[k].thankNote.trim()||d.areas[k].askNote.trim()));}
function browse(entries,{query='',type='',status='',tag='',from='',to=''}={}){const q=query.trim().toLowerCase();return entries.filter(d=>(!q||[d.topic,...d.tags].join(' ').toLowerCase().includes(q))&&(!type||d.entryType===type)&&(!status||d.answerStatus===status)&&(!tag||d.tags.includes(tag))&&(!from||dateOnly(d.prayedAt)>=from)&&(!to||dateOnly(d.prayedAt)<=to)).sort((a,b)=>Date.parse(b.prayedAt||b.createdAt)-Date.parse(a.prayedAt||a.createdAt));}
function dateOnly(iso){if(!validDate(iso))return '';return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Singapore',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(iso));}
function localInput(iso){if(!validDate(iso))return '';const p=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Singapore',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(iso));const d=Object.fromEntries(p.map(x=>[x.type,x.value]));return `${d.year}-${d.month}-${d.day}T${d.hour}:${d.minute}`;}
function fromInput(s){if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(s))throw Error('Enter a valid prayer date and time.');const d=new Date(s+':00+08:00');if(!validDate(d.toISOString())||localInput(d.toISOString())!==s)throw Error('Enter a valid prayer date and time.');return d.toISOString();}
function restore(data,entries){let incoming;if(data.version===3)incoming=decode(JSON.stringify(data));else if(data.version===2)incoming=C.decode(JSON.stringify(data)).map(normalise);else throw Error('Use a Wholehearted version 2 or 3 JSON journal backup.');const ids=new Set(entries.map(x=>x.id));const additions=incoming.filter(x=>!ids.has(x.id));if(entries.length+additions.length>MAX)throw Error('The combined journal would exceed 100 entries. Nothing was imported.');return {entries:[...additions,...entries],added:additions.length,skipped:incoming.length-additions.length};}
const api={STORAGE,VERSION,MAX,TYPES,FORMS,STATUSES,tags,blank,normalise,decode,read,write,upsert,follow,compose,meaningful,browse,dateOnly,localInput,fromInput,restore};if(typeof module==='object'&&module.exports)module.exports=api;else root.WholeheartedJournal=api;
})(globalThis);