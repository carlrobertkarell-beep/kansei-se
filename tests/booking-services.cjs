/* Run the real public consent bridge in a VM; never send test traffic to Google. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root,'assets/analytics.20261031.js'),'utf8');
function fixture(saved = {}, host = 'www.kansei.se') {
 const storage=new Map(Object.entries(saved)), handlers={}, scripts=[], nodes=[];
 const node=()=>({hidden:false,listeners:{},setAttribute(){},focus(){},append(){},
   querySelector(){return {focus(){}};},addEventListener(k,f){this.listeners[k]=f;}});
 const document={readyState:'complete',title:'Public page',cookie:'',referrer:'https://google.se/?private=never',
  querySelector(s){if(s.startsWith('meta'))return {content:'G-TEST123456'};if(s.startsWith('link'))return {href:'https://www.kansei.se/priser/?private=never#private'};return {append(){}};},
  body:{classList:{contains(){return true;}},append(n){nodes.push(n);}},
  head:{append(n){scripts.push(n);}},createElement(){return node();},addEventListener(k,f){handlers[k]=f;}};
 const window={addEventListener(k,f){handlers[k]=f;}},session=new Map();
 const context={window,document,location:{hostname:host,href:'https://'+host+'/priser/'},URL,Date,JSON,Number,
  localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
  sessionStorage:{getItem:k=>session.get(k)??null,setItem:(k,v)=>session.set(k,v),removeItem:k=>session.delete(k)}};
 vm.runInNewContext(source,context);
 const choose=allowed=>nodes[0].listeners.click({target:{closest(){return {dataset:{statistics:allowed?'yes':'no'}};}}});
 const emit=(service,placement='content')=>handlers['kansei:booking-intent']?.({detail:{event:'booking_click',service,placement,patient:'never',symptom:'never',url:'never'}});
 const events=()=>Array.from(window.dataLayer||[],args=>Array.from(args));
 return {window,document,storage,scripts,nodes,choose,emit,events,handlers};
}
const s=fixture({'kansei-statistics-v1':JSON.stringify({allowed:true,at:Date.now()})});
assert.equal(s.scripts.length,0,'Old consent must not enable newly expanded measurement');
s.emit('ultrasound');assert.equal(s.events().length,0);
s.choose(false);s.emit('ultrasound');assert.equal(s.events().length,0);
s.choose(true);assert.equal(s.scripts.length,1);
assert.equal(s.storage.has('kansei-statistics-v1'),false);
assert.equal(s.window.KanseiMeasure,true);
const mapping={ultrasound:'booking_ultrasound_click',hyaluron:'booking_hyaluron_click',naprapathy:'booking_naprapathy_click',prp:'booking_prp_click',consultation:'booking_consultation_click',wellness:'booking_wellness_click',general:'booking_general_click'};
for(const [service,event] of Object.entries(mapping)) {
 const before=s.events().length;s.emit(service,'price_list');
 const added=s.events().slice(before);
 assert.deepEqual(added.map(e=>e[1]),['booking_click',event]);
 for(const e of added){assert.equal(e[2].placement,'price_list');assert.equal(e[2].measurement_version,'20261031');assert(!JSON.stringify(e).includes('never'));assert(!('service'in e[2]));assert(!('booking_complete'in e[2]));}
}
s.emit('private-diagnosis','private-placement');
assert.deepEqual(s.events().slice(-2).map(e=>e[1]),['booking_click','booking_general_click']);
assert.equal(s.events().at(-1)[2].placement,'content');
assert(!JSON.stringify(s.events()).includes('private'));
const n=s.events().length;s.choose(false);s.emit('hyaluron');assert.equal(s.events().length,n);
assert.equal(s.window.KanseiMeasure,false);
const preview=fixture({},'terminal.local');assert.equal(preview.nodes.length,0);assert.equal(preview.scripts.length,0);
// Classify actual service IDs with the clinic runtime, independently of page/label/attributes.
const clinic=fs.readFileSync(path.join(root,'assets/clinic.20261031.js'),'utf8');
const start=clinic.indexOf('          const serviceId=');
const end=clinic.indexOf('          const placement=',start);
assert(start>0&&end>start);
const classification=clinic.slice(start,end)+'\nservice;';
for(const [id,expected] of Object.entries({'3263299':'naprapathy','1946824':'ultrasound','3409516':'hyaluron','3478216':'hyaluron','3409514':'prp','3409513':'consultation','1952697':'wellness','48847':'general','999':'general'})) {
 const destination=new URL('https://www.bokadirekt.se/boka-tjanst/kansei-48847/visit-'+id);
 assert.equal(vm.runInNewContext(classification,{destination}),expected);
}
assert.equal(vm.runInNewContext(classification,{destination:new URL('https://www.bokadirekt.se/places/clinic-1946824')}),'general');
console.log('PASS: new consent, rejection, withdrawal, one base event plus one service breakdown, allowlisted payloads, preview exclusion and exact destination-ID classification.');
