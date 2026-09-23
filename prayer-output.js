/* Response-format checks, not a judgement of the prayer or the person. No network or storage. */
(function(root){'use strict';
const KINDS=['sentence','whems','extended'];
const NAMES={W:'Will',H:'Heart',E:'Emotions',M:'Mind',S:'Soul'};
const LABELS={sentence:'One-sentence prayer',whems:'W.H.E.M.S. prayer',extended:'Extended prayer'};
const MAX={sentence:6000,whems:16000,extended:24000};
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
function fieldStatus(state,code,message){return {state,code,message};}
function inspect(raw,target='all'){
 const values={},statuses={};const wanted=KINDS.includes(target)?[target]:KINDS;
 for(const kind of wanted){
  let value=raw?.[kind];let missing=[];
  if(kind==='whems'&&object(value)){
   missing=Object.keys(NAMES).filter(k=>typeof value[k]!=='string'||!value[k].trim());
   if(Object.keys(NAMES).some(k=>value[k]!==undefined&&(typeof value[k]!=='string'||value[k].length>MAX.whems))){statuses[kind]=fieldStatus('invalid','OUTPUT_INVALID','The W.H.E.M.S. response contained an invalid section. Your previous prayer was kept.');continue;}
   value=Object.entries(NAMES).filter(([k])=>typeof value[k]==='string'&&value[k].trim()).map(([k,n])=>`${k} - ${n}\n${value[k].trim()}`).join('\n\n');
  }
  if(value===undefined||value===null||value===''){statuses[kind]=fieldStatus('missing','OUTPUT_MISSING',`${LABELS[kind]} was not returned. This is a response problem, not a missing personal reflection.`);continue;}
  if(typeof value!=='string'||value.length>MAX[kind]){statuses[kind]=fieldStatus('invalid','OUTPUT_INVALID',`${LABELS[kind]} could not be read safely. Your previous wording was kept.`);continue;}
  value=value.trim();if(!value){statuses[kind]=fieldStatus('missing','OUTPUT_MISSING',`${LABELS[kind]} was empty. You may retry this form or use a local starting prayer.`);continue;}
  values[kind]=value;
  if(kind==='whems'&&!missing.length){
   // Recognise harmless legacy heading presentation without inventing missing prayer text.
   const plain=value.replace(/^\s{0,3}#{1,6}\s*/gm,'').replace(/\*\*|__/g,'');
   missing=Object.entries(NAMES).filter(([k,n])=>!new RegExp('(?:^|\\n)\\s*(?:'+k+'\\s*[-–—:.]\\s*(?:'+n+')?|' +n+'\\s*(?:[:.]|$))','im').test(plain)).map(([k])=>k);
  }
  if(missing.length){statuses[kind]=fieldStatus('incomplete','WHEMS_SECTIONS_MISSING','The returned prayer is missing: '+missing.map(k=>NAMES[k]).join(', ')+'. The received text is retained as a draft; no personal answers are required in every area.');continue;}
  const count=value.split(/\s+/).length;
  if(kind==='extended'&&count<300){statuses[kind]=fieldStatus('incomplete','EXTENDED_SHORT',`A shorter draft was returned (${count} words), rather than the requested extended form. You may use it, edit it, or retry only this form. Longer is not spiritually better.`);continue;}
  statuses[kind]=fieldStatus('ready','READY','Ready to review. Check that these words faithfully express your concern.');
 }
 return {values,statuses,complete:wanted.every(k=>statuses[k]?.state==='ready')};
}
function acceptedMetadata(raw){const out={};if(!object(raw))return out;
 for(const kind of KINDS){const x=raw[kind];if(!object(x))continue;out[kind]={origin:typeof x.origin==='string'?x.origin.slice(0,100):'',state:['ready','incomplete','local','edited','missing','invalid','preserved'].includes(x.state)?x.state:'edited',message:typeof x.message==='string'?x.message.slice(0,900):''};}return out;
}
const api={KINDS,NAMES,LABELS,MAX,inspect,acceptedMetadata};if(typeof module==='object'&&module.exports)module.exports=api;else root.WholeheartedPrayerOutput=api;
})(globalThis);
