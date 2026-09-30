// Real shared email helper + contact handler, with network mocked. No email sent.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const values = {name:'Review & Test',role:'R&D',company:'Example + Co',email:'review@example.com',topic:'Request Demo/PoC',message:'Line 1\nLine 2: 50% & more?',_honey:''};
const elements = Object.fromEntries(Object.entries(values).map(([k,v])=>[k,{value:v}]));
let submit, resets=0, calls=[], behavior='success', resolvePending;
const button={disabled:true,textContent:''};
const status={textContent:'',classList:{add(){}}};
const form={elements,reportValidity:()=>true,reset(){resets++;},querySelector:s=>s==='button[type="submit"]'?button:status,addEventListener(type,fn){submit=fn;}};
const window={AIRA_CONFIG:{recipient:'info@airafusion.com',emailSubject:'AIRA website enquiry'}};
const context={window,document:{querySelector:()=>form},location:{origin:'https://airafusion.com',pathname:'/contact.html'},AbortController,setTimeout,clearTimeout,fetch:async(url,options)=>{
  calls.push({url,payload:JSON.parse(options.body)});
  if(behavior==='offline') throw Error('offline');
  if(behavior==='pending') return new Promise(r=>{resolvePending=r;});
  return {ok:true,json:async()=>({success:behavior==='success'?'true':'false'})};
}};
for(const file of ['aira-email.js','aira-contact.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/static/js',file),'utf8'),context);
const send=()=>submit({preventDefault(){}});
(async()=>{
  assert.equal(button.disabled,false);
  await send();
  assert.equal(calls[0].url,'https://formsubmit.co/ajax/info%40airafusion.com');
  for(const [key,value] of Object.entries(values)) assert.equal(calls[0].payload[key],value);
  assert.equal(calls[0].payload._subject,window.AIRA_CONFIG.emailSubject);
  assert.equal(calls[0].payload.source,'Contact Us');
  assert.equal(calls[0].payload.conversation,undefined);
  assert.equal(resets,1);
  assert.match(status.textContent,/accepted/);
  for(const failure of ['offline','rejected']) {
    behavior=failure;await send();assert.equal(resets,1);assert.equal(button.disabled,false);assert.match(status.textContent,/couldn’t confirm/);
  }
  window.AIRA_CONFIG.recipient='';const count=calls.length;await send();assert.equal(calls.length,count);assert.match(status.textContent,/not available/);
  window.AIRA_CONFIG.recipient='other@example.com';behavior='pending';
  const first=send();await send();assert.equal(calls.length,count+1);assert.equal(button.disabled,true);
  assert.match(calls.at(-1).url,/other%40example.com$/);
  resolvePending({ok:true,json:async()=>({success:true})});await first;
  elements._honey.value='spam';await send();assert.equal(calls.length,count+1);
  console.log('PASS: shared recipient/config, all contact fields, mocked delivery, failures, duplicate prevention and honeypot; no email sent');
})().catch(error=>{console.error(error);process.exitCode=1;});
