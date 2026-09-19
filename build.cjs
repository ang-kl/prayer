'use strict';
// No packages or network needed; publish only the browser assets.
const fs = require('node:fs');
const path = require('node:path');
const out = path.join(__dirname, 'public');
fs.mkdirSync(out, {recursive:true});
for (const file of ['index.html','core.js','app.js','styles.css']) {
  fs.copyFileSync(path.join(__dirname,file), path.join(out,file));
}
console.log('Wholehearted static build: 4 assets copied to public/.');
