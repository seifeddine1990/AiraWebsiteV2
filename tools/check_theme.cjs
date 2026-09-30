// Verify startup preferences and blocked-storage behavior without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../src/static/js/theme.js'), 'utf8');

for (const [fallback, saved, blocked, expected] of [
  ['light', null, false, 'light'], ['dark', null, false, 'dark'],
  ['light', 'dark', false, 'light'], ['dark', 'light', false, 'dark'],
  ['light', 'invalid', false, 'light'], ['dark', null, true, 'dark'],
]) {
  let ready, click, stored = saved;
  const attrs = { 'data-default-theme': fallback };
  const sheet = {}, meta = {}, label = {};
  const button = { hidden: true, setAttribute() {}, querySelector: () => label,
    addEventListener(type, fn) { click = fn; } };
  const document = {
    documentElement: { getAttribute: key => attrs[key], setAttribute: (key, value) => attrs[key] = value },
    getElementById: () => sheet,
    querySelector: selector => selector === '.theme-toggle' ? button : meta,
    addEventListener(type, fn) { ready = fn; },
  };
  const localStorage = {
    getItem() { if (blocked) throw Error('Storage blocked'); return stored; },
    setItem(key, value) { if (blocked) throw Error('Storage blocked'); stored = value; },
  };
  vm.runInNewContext(source, { document, localStorage });
  assert.equal(attrs['data-theme'], expected);
  assert.equal(sheet.media, expected === 'light' ? 'all' : 'not all');
  ready();
  assert.equal(button.hidden, true);
  assert.equal(click, undefined);
  assert.equal(stored, saved);
}
console.log('PASS: light/dark defaults, ignored saved preferences, hidden toggle and blocked storage');
