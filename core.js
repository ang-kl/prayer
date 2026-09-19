/* Wholehearted: pure content, prayer composition and defensive persistence. */
(function (root) {
  'use strict';
  const KEYS = ['W', 'H', 'E', 'M', 'S'];
  const STORAGE = 'wholehearted-journal-v2';
  const LEGACY = 'wholehearted-prayer-v1';
  const VERSION = 2;
  const DESCRIPTION = 'W.H.E.M.S. Prayer brings our Will, Heart, Emotions, Mind and Soul before God when seeking his help and direction. We thank him for the areas he has already shaped and ask him to transform the areas that are still struggling, so that our decision and response honour Christ.';
  const AREAS = [
    {key:'W', name:'Will', question:'What am I willing to do?', help:'Bring your preferred outcome and your willingness to obey. Ask for help where obedience is costly.', thank:'the willingness to take a faithful step', ask:'be willing to obey you, even when it is difficult', passage:'Luke 22:42', context:'Jesus brings his request to the Father and submits to the Father\'s will.', step:'Luke.22.42', blb:'luk/22'},
    {key:'H', name:'Heart', question:'Why do I want this?', help:'Consider what you love, desire or protect. Bring mixed motives honestly, without assuming that every desire is wrong.', thank:'the love and concern you are growing in me', ask:'examine my motives and grow my love for you and others', passage:'Psalm 139:23-24', context:'The psalmist invites God to examine him and lead him.', step:'Ps.139.23', blb:'psa/139'},
    {key:'E', name:'Emotions', question:'What am I feeling?', help:'Name fear, joy, hurt or hope. Difficult feelings are not a verdict on your faith. Ask for help with your response.', thank:'the help you have given me in responding to my feelings', ask:'bring my feelings honestly to you and respond with patience and gentleness', passage:'Matthew 26:37-39', context:'Jesus experiences deep sorrow while praying in submission to his Father.', step:'Matt.26.38', blb:'mat/26'},
    {key:'M', name:'Mind', question:'What is true and wise?', help:'Separate facts from assumptions. What do Scripture, your responsibilities and sound counsel help you see?', thank:'the understanding and counsel you have provided', ask:'understand your Word, check my assumptions and receive wise counsel', passage:'Romans 12:1-2', context:'Paul connects a life offered to God with renewed thinking and discernment.', step:'Rom.12.2', blb:'rom/12'},
    {key:'S', name:'Soul', question:'Whose am I?', help:'Bring your whole life and allegiance before God. This is a foundation for prayer, not a score or a test of whether you are saved.', thank:'the opportunity to turn to you with my whole life', ask:'understand what it means to trust Christ and live for him', passage:'Ephesians 2:8-10', context:'Salvation is God\'s gift by grace through faith; good works follow rather than earn it.', step:'Eph.2.8', blb:'eph/2'}
  ];
  const FRUIT = ['Love','Joy','Peace','Patience','Kindness','Goodness','Faithfulness','Gentleness','Self-control'];
  const GATES = {
    forbidden:['I recognise a biblical prohibition','Name the teaching and check its context. Prayer is not permission to do what Scripture forbids.'],
    commanded:['I recognise a biblical responsibility','Name the responsibility and consider how to fulfil it wisely. Distress need not prevent obedience.'],
    principles:['I see principles to consider','Consider the facts, your responsibilities and wise counsel. A feeling of peace alone does not settle a decision.'],
    unsure:['I am not sure yet','Ask for wisdom, read the passage in context and speak with a trusted mature Christian. Uncertainty is not a verdict from God.']
  };
  const own = (o,k) => Object.prototype.hasOwnProperty.call(o,k);
  const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const text = (x,n=2000) => typeof x === 'string' ? x.slice(0,n) : '';
  const copy = x => JSON.parse(JSON.stringify(x));
  const natural = xs => xs.length < 2 ? (xs[0] || '') : xs.slice(0,-1).join(', ') + ' and ' + xs[xs.length-1];
  const esv = ref => 'https://www.esv.org/verses/' + encodeURIComponent(ref).replace(/%20/g,'+').replace(/%3A/g,':') + '/';
  const step = ref => 'https://www.stepbible.org/?q=' + encodeURIComponent('version=ESV|reference=' + ref);
  function blank(mode='seek', now=new Date().toISOString(), id) {
    return {id:id || ('p-' + (globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2))), mode:mode === 'thanks' ? 'thanks' : 'seek', topic:'', context:'', gate:'', scripture:'', belonging:'', areas:Object.fromEntries(KEYS.map(k=>[k,{thank:false,ask:false,thankNote:'',askNote:''}])), fruit:[], prayer:null, nextStep:'', revisit:'', createdAt:now, updatedAt:now, parentId:null, legacyNote:''};
  }
  function normalise(raw) {
    if (!object(raw) || typeof raw.id !== 'string' || !/^[a-zA-Z0-9_-]{1,100}$/.test(raw.id) || !object(raw.areas)) throw Error('Invalid prayer record.');
    const d = blank(raw.mode, text(raw.createdAt,40), raw.id);
    for (const k of ['topic','context','scripture','nextStep','legacyNote']) d[k] = text(raw[k], k==='topic'?500:2000);
    d.updatedAt = text(raw.updatedAt,40);
    d.gate = own(GATES,raw.gate) ? raw.gate : '';
    d.belonging = ['trusting','exploring','private'].includes(raw.belonging) ? raw.belonging : '';
    d.revisit = /^\d{4}-\d{2}-\d{2}$/.test(raw.revisit) ? raw.revisit : '';
    d.parentId = typeof raw.parentId === 'string' && /^[a-zA-Z0-9_-]{1,100}$/.test(raw.parentId) ? raw.parentId : null;
    d.prayer = typeof raw.prayer === 'string' ? raw.prayer.slice(0,30000) : null;
    d.fruit = FRUIT.filter(f=>Array.isArray(raw.fruit) && raw.fruit.includes(f));
    for (const k of KEYS) {
      if (!object(raw.areas[k])) throw Error('Incomplete prayer record.');
      const a = raw.areas[k];
      d.areas[k] = {thank:a.thank===true,ask:a.ask===true,thankNote:text(a.thankNote),askNote:text(a.askNote)};
    }
    return d;
  }
  function compose(d) {
    const lines = ['Father,', d.mode==='thanks' ? 'I return to you with this matter: ' + d.topic.trim() : 'I bring this decision before you: ' + d.topic.trim()];
    if (d.context.trim()) lines.push('Here is what I am carrying: ' + d.context.trim());
    if (d.belonging==='trusting') lines.push('Thank you for your grace in Christ. Help me live as someone who belongs to him.');
    else if (d.belonging==='exploring') lines.push('Help me understand the good news of Jesus and what it means to trust him.');
    for (const a of AREAS) {
      const r = d.areas[a.key];
      if (r.thank) lines.push(r.thankNote.trim() ? 'For my ' + a.name.toLowerCase() + ', I thank you for:\n' + r.thankNote.trim() : 'Thank you for ' + a.thank + '.');
      if (r.ask) lines.push(r.askNote.trim() ? 'For my ' + a.name.toLowerCase() + ', I ask for your help:\n' + r.askNote.trim() : 'Please help me ' + a.ask + '.');
    }
    if (d.fruit.length) lines.push('By your Spirit, grow ' + natural(d.fruit.map(f=>f.toLowerCase())) + ' in how I respond.');
    if (d.gate==='forbidden') lines.push('Where your Word forbids my proposed action, help me turn from it rather than seek permission for it.');
    if (d.gate==='commanded') lines.push('Help me fulfil what you require with wisdom and love.');
    lines.push('Keep me teachable through your Word. Help my decision and response honour Christ, and help me entrust the outcome to you.','In Jesus\' name, amen.');
    return lines.join('\n\n');
  }
  function guidance(d) {
    // This is a prompt based on the user's selection, never a moral classifier.
    if (!own(GATES,d.gate)) return {title:'No Scripture assessment recorded',body:'Begin by reading Scripture in context and asking for wisdom. The app has not assessed whether the proposed action is right.'};
    const key = d.gate;
    return {title:GATES[key][0],body:GATES[key][1]};
  }
  function review(prior, now, id) {
    const d = blank('thanks',now,id);
    d.topic = prior.topic;
    d.parentId = prior.id;
    return d; // No prior improvement, belief or answer is inferred.
  }
  function decode(raw) {
    if (raw === null) return [];
    if (typeof raw !== 'string' || raw.length > 2000000) throw Error('Saved data is too large or invalid.');
    const data = JSON.parse(raw);
    if (!object(data) || data.version!==VERSION || !Array.isArray(data.entries) || data.entries.length>100) throw Error('Unrecognised journal format.');
    const entries = data.entries.map(normalise);
    if (new Set(entries.map(e=>e.id)).size !== entries.length) throw Error('Duplicate prayer identifiers.');
    return entries;
  }
  function read(storage) {
    try { const raw=storage.getItem(STORAGE); return {ok:true,raw,entries:decode(raw),error:''}; }
    catch { return {ok:false,raw:null,entries:[],error:'Saved prayers could not be read. Existing data has not been changed. You can still pray and download your words.'}; }
  }
  function write(storage, entries, expectedRaw) {
    try {
      const current = storage.getItem(STORAGE);
      if (current !== expectedRaw) return {ok:false,error:'Your journal changed in another tab. Download this prayer, then reload before saving again.'};
      decode(current); // Refuse to overwrite unreadable or future-version data.
      const raw = JSON.stringify({version:VERSION,entries:entries.map(normalise)});
      decode(raw);
      storage.setItem(STORAGE,raw);
      if (storage.getItem(STORAGE)!==raw) return {ok:false,error:'Save could not be verified. Download a copy before leaving.'};
      return {ok:true,raw,entries:decode(raw),error:''};
    } catch { return {ok:false,error:'Not saved: browser storage is unavailable, full or unreadable. Your current prayer is still on screen; download a copy.'}; }
  }
  function upsert(entries,d,now=new Date().toISOString()) {
    const saved = normalise({...d,updatedAt:now});
    if (!saved.topic.trim()) throw Error('Please name the matter before saving.');
    const next=entries.filter(e=>e.id!==saved.id);
    if (next.length>=100) throw Error('The journal is full. Download a backup and remove an older prayer before saving.');
    return [saved,...next];
  }
  function migrate(raw, now=new Date().toISOString()) {
    const old=JSON.parse(raw);
    if (!object(old) || typeof old.decision!=='string' || !old.decision.trim()) throw Error('Earlier prayer not recognised.');
    const d=blank('seek',typeof old.savedAt==='string'?old.savedAt:now,'legacy-v1');
    d.topic=text(old.decision,500); d.context=text(old.why); d.nextStep=text(old.nextStep);
    // v1 merged commands and prohibitions; do not guess which was intended.
    d.gate=old.scriptureStatus==='principles'?'principles':'unsure';
    d.fruit=FRUIT.filter(f=>Array.isArray(old.fruit)&&old.fruit.includes(f));
    for(const k of KEYS) {
      const a=old.whems?.[k]; if(!object(a)) continue;
      if(a.status==='aligned') { d.areas[k].thank=true; d.areas[k].thankNote=text(a.note); }
      else if(['struggling','unclear'].includes(a.status)) { d.areas[k].ask=true; d.areas[k].askNote=text(a.note); }
    }
    d.legacyNote=text(old.review?.note);
    return d;
  }
  function exportText(d) {
    return ['Wholehearted | W.H.E.M.S. Prayer',d.topic,d.prayer ?? compose(d),d.scripture?'My Scripture reflection: '+d.scripture:'',d.nextStep?'My next faithful step: '+d.nextStep:'',d.revisit?'Revisit on: '+d.revisit+' (no reminder scheduled)':'','A prayer aid, not a message from God. Scripture remains the authority.'].filter(Boolean).join('\n\n');
  }
  const api={KEYS,STORAGE,LEGACY,VERSION,DESCRIPTION,AREAS,FRUIT,GATES,copy,esv,step,blank,normalise,compose,guidance,review,decode,read,write,upsert,migrate,exportText};
  if(typeof module==='object' && module.exports) module.exports=api; else root.WholeheartedCore=api;
})(typeof globalThis!=='undefined'?globalThis:this);
