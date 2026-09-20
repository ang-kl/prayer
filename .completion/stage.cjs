'use strict';
// Temporary, exact-source staging. Only blobs and a tree are written to this repository.
// No commit/ref/deployment is changed here. No personal data or API secrets are included.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib');
const root='/tmp/wholehearted-stage',repo='ang-kl/prayer';
const payload=[0,1,2,3].map(i=>fs.readFileSync(path.join(__dirname,'part-'+i+'.txt'),'utf8')).join('');
if(crypto.createHash('sha256').update(payload).digest('hex')!=='add09eb90f779451ac84b8e90beecae9cb6915756cde4dfc50bf4188159d679c')throw Error('Transport integrity failure');
const manifest=JSON.parse(zlib.brotliDecompressSync(Buffer.from(payload,'base64')).toString('utf8'));
const gitsha=b=>crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex');
async function api(endpoint,body){const r=await fetch('https://api.github.com/repos/'+repo+'/git/'+endpoint,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+process.env.GITHUB_TOKEN,'Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'},body:body?JSON.stringify(body):undefined});if(!r.ok)throw Error('Repository staging API '+r.status);return r.json();}
async function blob(sha){const v=await api('blobs/'+sha);if(v.encoding!=='base64')throw Error('Unexpected blob encoding');const b=Buffer.from(v.content,'base64');if(gitsha(b)!==sha)throw Error('Source blob integrity failure');return b;}
(async()=>{
 if(!['prepare','publish'].includes(process.argv[2]))throw Error('Choose prepare or publish');
 if(process.env.GITHUB_REPOSITORY!==repo||process.env.GITHUB_REF!=='refs/heads/completion/wholehearted-0-0-002')throw Error('Unexpected repository or branch');
 const names=new Set();for(const e of manifest){if(!/^[a-zA-Z0-9_.\/-]+$/.test(e.path)||e.path.startsWith('/')||e.path.split('/').includes('..')||names.has(e.path))throw Error('Invalid path');names.add(e.path);}
 if(process.argv[2]==='prepare'){
  fs.mkdirSync(root,{recursive:true});for(const e of manifest){let data;
   if(e.text!==undefined)data=Buffer.from(e.text,'utf8');
   else if(e.ops){const original=await blob(e.baseSha),chunks=[];let at=0;for(const [start,end,b64] of e.ops){if(start<at||end<start||end>original.length)throw Error('Invalid patch bounds');chunks.push(original.subarray(at,start),Buffer.from(b64,'base64'));at=end;}chunks.push(original.subarray(at));data=Buffer.concat(chunks);}
   else data=await blob(e.sha);
   if(gitsha(data)!==e.sha)throw Error('Prepared content mismatch: '+e.path);
   const out=path.join(root,e.path);fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,data);
  }console.log('PREPARED_EXACT_FILES',manifest.length);return;
 }
 const tree=[];for(const e of manifest){const b=fs.readFileSync(path.join(root,e.path));if(gitsha(b)!==e.sha)throw Error('Tested source changed: '+e.path);if(e.ops||e.text!==undefined){const made=await api('blobs',{content:b.toString('base64'),encoding:'base64'});if(made.sha!==e.sha)throw Error('Published hash mismatch');}tree.push({path:e.path,mode:'100644',type:'blob',sha:e.sha});}
 const result=await api('trees',{tree});console.log('VERIFIED_COMPLETION_TREE',result.sha);console.log('VERIFIED_COMPLETION_FILES',tree.length);
})().catch(e=>{console.error(e.message);process.exitCode=1;});
