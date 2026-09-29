// Exercise the real contact handler without opening a mail client or sending mail.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const values = {
  name: 'Review & Test', role: 'R&D', company: 'Example + Co',
  email: 'review@example.com', topic: 'Request Demo/PoC',
  message: 'First line\nSecond line: 50% & more?',
};
let submit, confirmed = false, prevented = false;
const form = {
  addEventListener(type, fn) { if (type === 'submit') submit = fn; },
  getAttribute() { return 'info@airafusion.com'; },
  querySelector() { return { classList: { add() { confirmed = true; } } }; },
};
const document = {
  documentElement: { classList: { remove() {} } },
  querySelector(selector) { return selector === 'form[data-mailto]' ? form : null; },
  querySelectorAll() { return []; },
};
const window = { matchMedia: () => ({ matches: true }), addEventListener() {}, location: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/static/js/site.js'), 'utf8'), {
  document, window, FormData: class { get(key) { return values[key]; } },
});
submit({ preventDefault() { prevented = true; } });
const draft = new URL(window.location.href);
assert.equal(draft.protocol, 'mailto:');
assert.equal(draft.pathname, 'info@airafusion.com');
assert.equal(draft.searchParams.get('subject'), '[Request Demo/PoC] Example + Co');
assert.equal(draft.searchParams.get('body'), 'Name: Review & Test\nRole: R&D\nCompany: Example + Co\nEmail: review@example.com\n\nFirst line\nSecond line: 50% & more?');
assert(prevented && confirmed);
console.log('PASS: contact draft recipient, subject, fields, newlines and special-character encoding; no email sent');
