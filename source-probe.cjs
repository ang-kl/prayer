'use strict';
// Temporary preview-build diagnostics: inspect the official public embed; never print keys.
(async()=>{try{const r=await fetch('https://static.esvmedia.org/crossref/crossref.min.js',{signal:AbortSignal.timeout(10000)});const s=await r.text();console.log('PUBLIC_ESV_SCRIPT_STATUS',r.status);console.log('PUBLIC_ESV_SCRIPT_TAIL',s.slice(-16000));console.log('CONFIG_PRESENT',JSON.stringify({openai:!!process.env.openai_key,model:process.env.openai_model||null,esv:!!process.env.ESV_API_KEY}));}catch{console.log('SOURCE_PROBE_UNAVAILABLE');}})();
