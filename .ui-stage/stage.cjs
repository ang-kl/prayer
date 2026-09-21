'use strict';
// Temporary exact-source transport for this preview only. Does not change any ref,
// production deployment, settings, credentials or journal. Only source blobs are staged.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib');
const repo='ang-kl/prayer',root='/tmp/wholehearted-ui-stage';
const encoded=[0,1].map(n=>fs.readFileSync(path.join(__dirname,'part-'+n+'.txt'),'utf8')).join('');
if(crypto.createHash('sha256').update(encoded).digest('hex')!=='abfe2de5b1694c84bf6bbf232bb3eae5da724adcea2518d8dae83c522e97a885')throw Error('Source transport integrity failure');
const manifest=JSON.parse(zlib.brotliDecompressSync(Buffer.from(encoded,'base64')).toString('utf8'));
// Correct a test-runner argument, not application code: WebKit has no --no-sandbox switch.
const testFile=manifest.find(e=>e.path==='tests/experience-browser.py');
const oldLaunch="    kwargs={'args':['--no-sandbox']}\n    if os.environ.get('CHROMIUM_PATH'): kwargs['executable_path']=os.environ['CHROMIUM_PATH']\n    elif MODE=='dom': kwargs['executable_path']='/usr/bin/chromium'\n    browser=getattr(pw,os.environ.get('TEST_BROWSER','chromium')).launch(**kwargs)";
const newLaunch="    engine=os.environ.get('TEST_BROWSER','chromium')\n    kwargs={'args':['--no-sandbox']} if engine=='chromium' else {}\n    if engine=='chromium':\n      if os.environ.get('CHROMIUM_PATH'): kwargs['executable_path']=os.environ['CHROMIUM_PATH']\n      elif MODE=='dom': kwargs['executable_path']='/usr/bin/chromium'\n    browser=getattr(pw,engine).launch(**kwargs)";
if(!testFile||testFile.sha!=='8fbe1b7a2ee9829c06af2c2f52c8094a40c5380a')throw Error('Unexpected browser test source');
testFile.sha='c55be2db719634fcab18a22bc75066f00162c5a1';
const allowed=new Set(['experience.js','experience.css','journey-ui.js','app.js','theme.js','index.html','build.cjs','release.json','package.json','tests/about-introduction.test.cjs','tests/design-export.test.cjs','tests/journal.test.cjs','tests/completion-browser.py','tests/experience.test.cjs','tests/experience-browser.py','.github/workflows/preview-check.yml']);
const hash=b=>crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex');
async function api(endpoint,body){const r=await fetch('https://api.github.com/repos/'+repo+'/git/'+endpoint,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+process.env.GITHUB_TOKEN,'Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'},body:body?JSON.stringify(body):undefined});if(!r.ok)throw Error('Source-blob staging HTTP '+r.status);return r.json();}
async function original(sha){const r=await api('blobs/'+sha);if(r.encoding!=='base64')throw Error('Unexpected source encoding');const b=Buffer.from(r.content,'base64');if(hash(b)!==sha)throw Error('Source blob integrity failure');return b;}
(async()=>{
 if(process.env.GITHUB_REPOSITORY!==repo||process.env.GITHUB_REF!=='refs/heads/ui/guided-feedback-0-0-004')throw Error('Wrong staging repository or branch');
 if(manifest.length!==allowed.size||new Set(manifest.map(x=>x.path)).size!==allowed.size||manifest.some(x=>!allowed.has(x.path)))throw Error('Unexpected changed-file set');
 if(process.argv[2]==='prepare'){
   const source=path.resolve(__dirname,'..');
   fs.cpSync(source,root,{recursive:true,filter:p=>{const r=path.relative(source,p);return !['.git','.ui-stage','public','evidence'].some(x=>r===x||r.startsWith(x+'/'));}});
   for(const e of manifest){let b;
     if(e.text!==undefined)b=Buffer.from(e.text,'utf8');
     else{const old=await original(e.baseSha),parts=[];let at=0;for(const [start,end,insertion] of e.ops){if(start<at||end<start||end>old.length)throw Error('Invalid patch bounds');parts.push(old.subarray(at,start),Buffer.from(insertion,'utf8'));at=end;}parts.push(old.subarray(at));b=Buffer.concat(parts);}
     if(e===testFile){if(hash(b)!=='8fbe1b7a2ee9829c06af2c2f52c8094a40c5380a')throw Error('Original test hash mismatch');const s=b.toString('utf8');if(s.split(oldLaunch).length!==2)throw Error('Unexpected test launch');b=Buffer.from(s.replace(oldLaunch,newLaunch),'utf8');}
     if(hash(b)!==e.sha)throw Error('Prepared content mismatch: '+e.path);
     const file=path.join(root,e.path);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,b);
   }
   console.log('PREPARED_VERIFIED_CHANGED_FILES',manifest.length);return;
 }
 if(process.argv[2]!=='publish')throw Error('Choose prepare or publish');
 for(const e of manifest){const b=fs.readFileSync(path.join(root,e.path));if(hash(b)!==e.sha)throw Error('Tested source changed: '+e.path);const made=await api('blobs',{content:b.toString('base64'),encoding:'base64'});if(made.sha!==e.sha)throw Error('Published blob mismatch');console.log('VERIFIED_SOURCE_BLOB',e.path,e.sha);}
 console.log('All source blobs verified. No tree, commit or branch was changed by this job.');
})().catch(e=>{console.error(e.message);process.exitCode=1;});
