'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=__dirname,out=path.join(root,'public'),r=require('./release.json');
if(!Number.isSafeInteger(r.build)||r.build<1||!/^0\.0\.[1-9]\d*$/.test(r.packageVersion))throw Error('Invalid build identity.');
const version='0.0.'+String(r.build).padStart(3,'0');
const build={version,number:r.build,sourceCommit:process.env.VERCEL_GIT_COMMIT_SHA||process.env.SOURCE_COMMIT||null,builtAt:new Date().toISOString()};
// This directory is generated; never place personal prayer files in it.
fs.rmSync(out,{recursive:true,force:true});fs.mkdirSync(out,{recursive:true});
const assets=['index.html','theme.js','core.js','journal.js','catalogue.js','app.js','styles.css','export.js','about.js','guidance-core.js','journey-ui.js','experience.js','experience.css'];
for(const file of assets){if(file==='styles.css')fs.writeFileSync(path.join(out,file),require('./theme.js').css+'\n'+fs.readFileSync(path.join(root,file),'utf8'));else fs.copyFileSync(path.join(root,file),path.join(out,file));}
fs.writeFileSync(path.join(out,'build-info.js'),'window.WholeheartedBuild='+JSON.stringify(build)+';\n');
console.log('Wholehearted '+version+': '+(assets.length+1)+' browser assets. Server-only Scripture key is not bundled.');
