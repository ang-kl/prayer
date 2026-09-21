'use strict';
// Temporary exact-source verification. Only source blobs are published; no refs,
// production settings, API credentials, prayers or user data are accessed or changed.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib');
const repo='ang-kl/prayer',root='/tmp/wholehearted-prayer-stage';
const encoded=[0,1,2].map(n=>fs.readFileSync(path.join(__dirname,'part-'+n+'.txt'),'utf8')).join('');
if(crypto.createHash('sha256').update(encoded).digest('hex')!=='b4182fc6d92d705a3141a729e5e6ade2dbf7edbdd1327b664a3862f0362f2194')throw Error('Source transport integrity failure');
const manifest=JSON.parse(zlib.brotliDecompressSync(Buffer.from(encoded,'base64')).toString('utf8'));
const allowed=new Set(['.github/workflows/preview-check.yml','api/guidance.js','app.js','build.cjs','experience.css','experience.js','export.js','guidance-core.js','index.html','journey-ui.js','package.json','prayer-output.js','release.json','teaching.js','tests/about-introduction.test.cjs','tests/completion-browser.py','tests/design-export.test.cjs','tests/experience-browser.py','tests/experience.test.cjs','tests/inplace-browser.py','tests/journal.test.cjs','tests/prayer-output.test.cjs']);
const hash=b=>crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex');
async function api(endpoint,body){const r=await fetch('https://api.github.com/repos/'+repo+'/git/'+endpoint,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+process.env.GITHUB_TOKEN,'Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'},body:body?JSON.stringify(body):undefined});if(!r.ok)throw Error('Source-blob staging HTTP '+r.status);return r.json();}
async function original(sha){const r=await api('blobs/'+sha);if(r.encoding!=='base64')throw Error('Unexpected source encoding');const b=Buffer.from(r.content,'base64');if(hash(b)!==sha)throw Error('Source blob integrity failure');return b;}
(async()=>{
 if(process.env.GITHUB_REPOSITORY!==repo||process.env.GITHUB_REF!=='refs/heads/fix/inplace-prayers-0-0-005')throw Error('Wrong staging repository or branch');
 if(manifest.length!==allowed.size||new Set(manifest.map(x=>x.path)).size!==allowed.size||manifest.some(x=>!allowed.has(x.path)))throw Error('Unexpected changed-file set');
 if(process.argv[2]==='prepare'){
   const source=path.resolve(__dirname,'..');
   fs.cpSync(source,root,{recursive:true,filter:p=>{const r=path.relative(source,p);return !['.git','.prayer-stage','public','evidence'].some(x=>r===x||r.startsWith(x+'/'));}});
   fs.rmSync(path.join(root,'.github/workflows/prayer-stage.yml'),{force:true});
   for(const e of manifest){let b;
     if(e.text!==undefined)b=Buffer.from(e.text,'utf8');
     else{const old=await original(e.baseSha),parts=[];let at=0;for(const [start,end,insertion] of e.ops){if(start<at||end<start||end>old.length)throw Error('Invalid patch bounds');parts.push(old.subarray(at,start),Buffer.from(insertion,'utf8'));at=end;}parts.push(old.subarray(at));b=Buffer.concat(parts);}
     if(hash(b)!==e.sha)throw Error('Prepared content mismatch: '+e.path);
     const file=path.join(root,e.path);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,b);
   }
   console.log('PREPARED_VERIFIED_CHANGED_FILES',manifest.length);return;
 }
 if(process.argv[2]!=='publish')throw Error('Choose prepare or publish');
 for(const e of manifest){const b=fs.readFileSync(path.join(root,e.path));if(hash(b)!==e.sha)throw Error('Tested source changed: '+e.path);const made=await api('blobs',{content:b.toString('base64'),encoding:'base64'});if(made.sha!==e.sha)throw Error('Published blob mismatch');console.log('VERIFIED_SOURCE_BLOB',e.path,e.sha);}
 console.log('All source blobs verified. No tree, commit or branch was changed by this job.');
})().catch(e=>{console.error(e.message);process.exitCode=1;});
