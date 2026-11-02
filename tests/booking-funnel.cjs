/* VM-only tests: no network requests or events are sent to analytics services. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/booking-funnel.20261102.js'), 'utf8');

function fixture(options = {}) {
  let now = 0, next = 0;
  const timers = new Map(), handlers = {}, events = [], observers = [];
  const targets = Array.from({length: options.target === false ? 0 : options.markers || 1}, () => ({}));
  const location = new URL(options.url || 'https://www.kansei.se/hyaluronsyra/kna/?patient=never&gclid=never#private');
  const document = {
    hidden: false, referrer: 'https://google.se/search?patient=never', title: 'never',
    body: {classList: {contains: () => options.clinic !== false}},
    querySelector(selector) {
      if (selector.startsWith('meta')) return {content: options.id || 'G-TEST123456'};
      if (selector.startsWith('link')) return {href: options.canonical || location.href};
      return null;
    },
    querySelectorAll(selector) { return selector === '[data-booking-options]' ? targets : []; },
    addEventListener: (name, callback) => { handlers[name] = callback; }
  };
  class Observer {
    constructor(callback, settings) { this.callback = callback; this.settings = settings; this.disconnected = false; this.targets = []; observers.push(this); }
    observe(element) { this.targets.push(element); }
    disconnect() { this.disconnected = true; }
    show(ratio, index = 0) { if (!this.disconnected) this.callback([{target: this.targets[index], intersectionRatio: ratio, isIntersecting: ratio > 0}]); }
  }
  const window = {
    KanseiMeasure: options.consent === true,
    gtag: (...args) => events.push(args),
    setTimeout(callback, delay) { const id = ++next; timers.set(id, {callback, at: now + delay}); return id; },
    clearTimeout: id => timers.delete(id),
    setInterval(callback, delay) { const id = ++next; timers.set(id, {callback, at: now + delay, interval: delay}); return id; }
  };
  if (options.observer !== false) window.IntersectionObserver = Observer;
  const tick = duration => {
    const until = now + duration;
    for (;;) {
      let chosen;
      for (const [id, timer] of timers) if (timer.at <= until && (!chosen || timer.at < chosen[1].at)) chosen = [id, timer];
      if (!chosen) break;
      const [id, timer] = chosen; now = timer.at; timers.delete(id);
      if (timer.interval) timers.set(id, {...timer, at: now + timer.interval});
      timer.callback();
    }
    now = until;
  };
  vm.runInNewContext(source, {window, document, location, URL});
  const click = (href = '#boka', placement = '', region = '', prevented = false) => {
    const anchor = {dataset: {placement}, getAttribute: () => href, closest: selector => selector === region ? {} : null};
    handlers.click?.({defaultPrevented: prevented, target: {closest: () => anchor}});
  };
  return {window, document, observers, events, handlers, timers, tick, click};
}

const denied = fixture();
denied.tick(2000); denied.click();
assert.equal(denied.observers.length, 0); assert.equal(denied.events.length, 0);
denied.window.KanseiMeasure = true; denied.tick(250);
assert.equal(denied.observers.length, 1);
assert.deepEqual(Array.from(denied.observers[0].settings.threshold), [0, 0.25]);
denied.observers[0].show(0.24); denied.tick(2000); assert.equal(denied.events.length, 0);
denied.observers[0].show(0.25); denied.tick(999); assert.equal(denied.events.length, 0);
denied.tick(1); assert.equal(denied.events[0][1], 'booking_options_view');
assert.equal(denied.events[0][2].page_location, 'https://www.kansei.se/hyaluronsyra/kna/');
assert.equal(denied.events[0][2].page_referrer, 'https://google.se/');
assert.equal(denied.events[0][2].page_title, 'Hyaluroninjektion i knä i Stockholm');
assert.equal(denied.events[0][2].measurement_version, '20261102');
assert(!JSON.stringify(denied.events).includes('never'));
denied.observers[0].show(0); denied.observers[0].show(1); denied.tick(2000);
assert.equal(denied.events.length, 1, 'Only one price-section view per page');
denied.click('#boka', 'service_card'); assert.equal(denied.events.at(-1)[1], 'booking_options_open');
assert.equal(denied.events.at(-1)[2].placement, 'service_card');
denied.click('#pris', 'price_list'); assert.equal(denied.events.at(-1)[1], 'booking_options_open');
assert.equal(denied.events.at(-1)[2].placement, 'price_list');
const count = denied.events.length;
for (const href of ['#other', 'https://www.bokadirekt.se/#boka', '/ultraljud/axel/#boka', '?private=never#boka']) denied.click(href);
denied.click('#boka', '', '', true);
assert.equal(denied.events.length, count, 'Only actual same-page booking-option links are measured');
denied.window.KanseiMeasure = false; denied.click(); denied.tick(500);
assert.equal(denied.events.length, count);

const withdrawn = fixture({consent: true});
withdrawn.observers[0].show(1); withdrawn.tick(750);
withdrawn.window.KanseiMeasure = false; withdrawn.tick(500);
assert.equal(withdrawn.events.length, 0, 'Withdrawal cancels a pending visible dwell');
assert.equal(withdrawn.observers[0].disconnected, true);
withdrawn.window.KanseiMeasure = true; withdrawn.tick(250);
withdrawn.observers.at(-1).show(1); withdrawn.tick(1000);
assert.equal(withdrawn.events.length, 1, 'Fresh opt-in starts a new observation');

const interrupted = fixture({consent: true});
interrupted.observers[0].show(1); interrupted.tick(800); interrupted.observers[0].show(0);
interrupted.tick(1000); assert.equal(interrupted.events.length, 0);
interrupted.observers[0].show(1); interrupted.tick(600); interrupted.document.hidden = true;
interrupted.handlers.visibilitychange(); interrupted.tick(1000); assert.equal(interrupted.events.length, 0);
interrupted.document.hidden = false; interrupted.handlers.visibilitychange(); interrupted.tick(1000);
assert.equal(interrupted.events.length, 1);

const multiple = fixture({consent: true, markers: 2});
assert.equal(multiple.observers[0].targets.length, 2);
multiple.observers[0].show(1, 0); multiple.tick(700); multiple.observers[0].show(0, 0);
multiple.observers[0].show(1, 1); multiple.tick(300);
assert.equal(multiple.events.length, 0, 'Each marker must satisfy its own continuous dwell');
multiple.tick(700); assert.equal(multiple.events.length, 1);
multiple.observers[0].show(1, 0); multiple.tick(2000);
assert.equal(multiple.events.length, 1, 'Multiple markers still produce a single view per page');

for (const url of ['https://www.kansei.se/ultraljud/axel/', 'https://kansei.se/ultraljud/kna/']) {
  const page = fixture({consent: true, url, canonical: 'https://example.com/private?never'});
  page.click('#boka', 'private', '.site-header');
  assert.equal(page.events[0][2].placement, 'header');
  assert(page.events[0][2].page_location.startsWith('https://www.kansei.se/ultraljud/'));
}
const unsupported = fixture({consent: true, observer: false});
unsupported.tick(2000); unsupported.click();
assert.equal(unsupported.events.length, 1); assert.equal(unsupported.events[0][1], 'booking_options_open');
for (const options of [{url: 'https://preview.example/hyaluronsyra/kna/'}, {url: 'https://www.kansei.se/private/'}, {clinic: false}, {id: 'invalid'}]) {
  const excluded = fixture({...options, consent: true}); excluded.tick(2000); excluded.click();
  assert.equal(excluded.events.length, 0); assert.equal(excluded.timers.size, 0);
}
console.log('PASS: consent gate, later opt-in, withdrawal, visible dwell, once-per-page view, internal booking links, sanitized payloads and preview/path exclusion.');
