'use strict';
// Only an allowlisted public passage ID reaches Crossway. No journal fields are accepted.
const catalogue=require('../catalogue.js');
const pending=new Map(),cache=new Map();let minute=0,requests=0;
const ttl=10*60*1000;
async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
 if(req.method!=='GET'){res.setHeader('Allow','GET');return res.status(405).json({error:'Method not allowed.'});}
 const q=req.query||{};if(Object.keys(q).some(k=>k!=='id')||typeof q.id!=='string'||!catalogue.get(q.id))return res.status(400).json({error:'Choose a passage from the Scripture index.'});
 const token=process.env.ESV_API_KEY;
 if(!token)return res.status(200).json({id:q.id,translation:'ESV',mode:'crossway-embed',source:catalogue.get(q.id).esv});
 const item=catalogue.get(q.id),now=Date.now();
 const c=cache.get(item.id);if(c&&now-c.at<ttl)return res.status(200).json(c.data);
 const m=Math.floor(now/60000);if(m!==minute){minute=m;requests=0;}
 // Local warm-instance guard. Crossway applies the account-wide service limit.
 if(!pending.has(item.id)&&requests>=50)return res.status(429).json({error:'The Scripture service is busy. Please try again shortly.'});
 try{
  if(!pending.has(item.id)){
   requests++;
   const promise=(async()=>{
    const url=new URL('https://api.esv.org/v3/passage/text/');url.search=new URLSearchParams({q:item.ref,'include-headings':'false','include-footnotes':'false','include-passage-references':'true','include-verse-numbers':'true','include-short-copyright':'true','include-copyright':'true'}).toString();
    const response=await fetch(url,{headers:{Authorization:'Token '+token},signal:AbortSignal.timeout(8000)});
    if(!response.ok)throw Error('UPSTREAM');const json=await response.json();
    if(!Array.isArray(json.passages)||json.passages.length!==1||typeof json.passages[0]!=='string'||!json.passages[0].trim()||json.passages[0].length>100000)throw Error('INVALID_SOURCE');
    const data={id:item.id,reference:item.ref,translation:'ESV',text:json.passages[0],source:item.esv};cache.set(item.id,{at:Date.now(),data});return data;
   })();pending.set(item.id,promise);
  }
  const data=await pending.get(item.id);return res.status(200).json(data);
 }catch{return res.status(502).json({error:'The ESV text could not be loaded. Your prayer has not been changed. Please try again.'});}
 finally{pending.delete(item.id);}
}
module.exports=handler;
module.exports._reset=()=>{cache.clear();pending.clear();minute=0;requests=0;};
