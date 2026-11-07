/* Execute the actual analytics bridge with a stubbed Google queue; no network traffic. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/analytics.20261101.js'), 'utf8');
const base = 'https://www.kansei.se/ultraljud/axel/';
function fixture(query = '', saved = {}) {
  const storage = new Map(Object.entries(saved)), session = new Map(), handlers = {}, scripts = [], nodes = [];
  const node = () => ({hidden:false, listeners:{}, setAttribute(){}, focus(){}, append(){},
    querySelector(){return {focus(){}};}, addEventListener(k,f){this.listeners[k]=f;}});
  const document = {readyState:'complete', title:'Public page', cookie:'', referrer:'https://www.google.se/search?q=PRIVATE_QUERY',
    querySelector(s){if(s.startsWith('meta')) return {content:'G-TEST123456'};
      if(s.startsWith('link')) return {href:base+'?private=CANONICAL_SECRET#PRIVATE_FRAGMENT'}; return {append(){}};},
    body:{classList:{contains(){return true;}},append(n){nodes.push(n);}}, head:{append(n){scripts.push(n);}},
    createElement(){return node();}, addEventListener(k,f){handlers[k]=f;}};
  const window = {addEventListener(k,f){handlers[k]=f;}};
  vm.runInNewContext(source, {window, document, URL, Date, JSON, Number,
    location:{hostname:'www.kansei.se',href:base+query},
    localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    sessionStorage:{getItem:k=>session.get(k)??null,setItem:(k,v)=>session.set(k,v),removeItem:k=>session.delete(k)}});
  return {storage,session,scripts,nodes,window,
    choose(allowed){nodes[0].listeners.click({target:{closest(){return {dataset:{statistics:allowed?'yes':'no'}};}}});},
    events(){return Array.from(window.dataLayer||[],args=>Array.from(args));},
    booking(){handlers['kansei:booking-intent']({detail:{event:'booking_click',service:'ultrasound',placement:'header',patient:'PRIVATE_PATIENT'}});},
    guide(event){handlers['kansei:booking-guide']({detail:{event,area:'PRIVATE_AREA',symptom:'PRIVATE_SYMPTOM',goal:'PRIVATE_GOAL'}});}};
}
const choice = allowed => JSON.stringify({allowed,at:Date.now()});
const query = '?gbraid=0AAAA_VALID_AGGREGATE&gad_source=1&gad_campaignid=12345678901'
  +'&gclid=PRIVATE_CLICK&dclid=PRIVATE_DISPLAY&wbraid=PRIVATE_WEB_CLICK&gad_unknown=PRIVATE_OTHER'
  +'&utm_source=google&utm_medium=cpc&utm_campaign=PRIVATE_CAMPAIGN&utm_term=PRIVATE_SYMPTOM'
  +'&patient=PRIVATE_PATIENT#PRIVATE_FRAGMENT';
const f = fixture(query, {'kansei-statistics-v2':choice(true)});
assert.equal(f.scripts.length,0);assert.equal(f.events().length,0);assert.equal(f.session.size,0);
f.booking();assert.equal(f.events().length,0);
f.choose(true);assert.equal(f.scripts.length,1);
assert.equal(f.storage.has('kansei-statistics-v2'),false);
assert.equal(JSON.parse(f.storage.get('kansei-statistics-v3')).allowed,true);
const expected = base+'?gbraid=0AAAA_VALID_AGGREGATE&gad_source=1&gad_campaignid=12345678901';
const config = f.events().find(e=>e[0]==='config')[2];
assert.equal(config.page_location,expected);
const consent = f.events().find(e=>e[0]==='consent')[2];
assert.equal(consent.analytics_storage,'granted');
for(const key of ['ad_storage','ad_user_data','ad_personalization']) assert.equal(consent[key],'denied');
f.booking();
const events = f.events().filter(e=>e[0]==='event');
assert.deepEqual(events.map(e=>e[1]),['page_view','booking_click','booking_ultrasound_click']);
for(const e of events){assert.equal(e[2].page_location,expected);assert.equal(e[2].measurement_version,'20261101');}
assert(!JSON.stringify(f.events()).includes('PRIVATE'));
assert(!JSON.stringify([...f.session]).includes('AGGREGATE'));
assert(!JSON.stringify([...f.storage]).includes('AGGREGATE'));
assert(!JSON.stringify(f.events()).includes('utm_source'));
const count = f.events().length;f.choose(false);f.booking();assert.equal(f.events().length,count);assert.equal(f.session.size,0);
const guide = fixture(query);
guide.guide('booking_guide_start');
guide.guide('booking_guide_result_view');
assert.equal(guide.events().length,0);
guide.choose(true);
guide.guide('booking_guide_start');
guide.guide('PRIVATE_SYMPTOM');
guide.guide('booking_guide_result_view');
const guideEvents = guide.events().filter(e=>e[0]==='event' && e[1].startsWith('booking_guide_'));
assert.deepEqual(guideEvents.map(e=>e[1]), ['booking_guide_start','booking_guide_result_view']);
for (const [, , fields] of guideEvents) {
  assert.equal(fields.page_location,'https://www.kansei.se/hjalp-mig-boka/');
  assert.equal(fields.page_title,'Hjälp mig boka rätt | Kansei');
  assert.equal(fields.placement,'guide');
  assert.deepEqual(Object.keys(fields).sort(),
    ['measurement_version','page_location','page_referrer','page_title','placement','referral_group','send_to']);
}
assert(!JSON.stringify(guideEvents).includes('PRIVATE'));
guide.choose(false);
guide.guide('booking_guide_start');
assert.equal(guide.events().filter(e=>e[0]==='event' && e[1].startsWith('booking_guide_')).length,2);
for(const legacy of ['kansei-statistics-v1','kansei-statistics-v2']) {
  const declined = fixture(query,{[legacy]:choice(false)});
  assert.equal(declined.scripts.length,0);assert.equal(declined.nodes[0].hidden,true);
  const oldApproval = fixture(query,{[legacy]:choice(true)});
  assert.equal(oldApproval.scripts.length,0);assert.equal(oldApproval.nodes[0].hidden,false);
}
const current = fixture(query,{'kansei-statistics-v3':choice(true)});
assert.equal(current.scripts.length,1);
const mixedLegacy=fixture(query,{'kansei-statistics-v2':choice(true),'kansei-statistics-v1':choice(false)});
assert.equal(mixedLegacy.scripts.length,0);assert.equal(mixedLegacy.nodes[0].hidden,false);
const cases = [
  ['?gclid=PRIVATE_CLICK&wbraid=PRIVATE_CLICK',base],
  ['?utm_source=google&utm_medium=cpc&utm_campaign=PRIVATE_CAMPAIGN&utm_term=PRIVATE_QUERY',base+'?utm_source=google&utm_medium=cpc'],
  ['?utm_source=google&utm_medium=organic',base],
  ['?utm_source=google&utm_medium=cpc&utm_source=attacker',base],
  ['?utm_source=Google&utm_medium=CPC',base],
  ['?gad_source=1&gad_source=2&gbraid=PRIVATE%26query&gad_campaignid=BAD',base],
  ['?gbraid='+('a'.repeat(513))+'&gad_source=1234&gad_campaignid='+('9'.repeat(21)),base],
  ['?gad_source=1&utm_source=google&utm_medium=cpc',base+'?gad_source=1'],
  ['?gad_campaignid=000123',base+'?gad_campaignid=000123'],
  ['?gad_source=%31&private=PRIVATE_QUERY',base+'?gad_source=1'],
  ['?gad_rogue=1&patient=PRIVATE_PATIENT#PRIVATE_FRAGMENT',base]
];
for(const [query,expected] of cases) {
  const c=fixture(query);c.choose(true);
  assert.equal(c.events().find(e=>e[0]==='config')[2].page_location,expected,query);
  assert(!JSON.stringify(c.events()).includes('PRIVATE'));
}
console.log('PASS: aggregate attribution, parameter validation, consent and withdrawal, booking intent and guide events without guide choices.');
