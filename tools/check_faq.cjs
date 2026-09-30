const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root=path.resolve(__dirname,'..');
const window={};
vm.runInNewContext(fs.readFileSync(path.join(root,'src/static/js/aira-faq.js'),'utf8'),{window});
assert(window.AIRA_FAQS.length>0);
const labels=new Set();
for(const faq of window.AIRA_FAQS){
  assert(faq.label && faq.answer && faq.keywords.length, 'Incomplete FAQ');
  assert(!labels.has(faq.label), 'Duplicate FAQ button');labels.add(faq.label);
  assert(faq.keywords.every(term=>typeof term==='string' && term.trim()), 'Empty keyword');
  assert(/^[a-z0-9/_-]+\.html(?:#[a-z0-9_-]+)?$/i.test(faq.page), 'FAQ must link to a local page');
  const [page,anchor]=faq.page.split('#');
  const content=fs.readFileSync(path.join(root,'src/pages',page),'utf8');
  if(anchor) assert(content.includes(`id="${anchor}"`),'Missing FAQ anchor');
}
console.log(`PASS: ${labels.size} FAQ entries, keywords and source links`);
