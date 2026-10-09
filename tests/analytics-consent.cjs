/* Prototype browser checks; no live Analytics requests are permitted. */
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.KANSEI_CHROMIUM||'/workspace/scratch/d152b02a2d39/medianus-review/browser/chromium',headless:true,args:['--no-sandbox']});
 const fixture=id=>'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="kansei-ga4" content="'+id+'"><link rel="canonical" href="https://www.kansei.se/for-vardgivare/?secret=removed#private"><link rel="stylesheet" href="/assets/analytics.20261009.css"><title>För vårdgivare | Kansei</title><script defer src="/assets/analytics.20261009.js"></script></head><body class="clinic-site"><main><h1>För vårdgivare</h1><a href="https://www.bokadirekt.se/places/clinic">Boka</a></main><footer class="footer"></footer></body></html>';
 async function setup(id='G-TEST123456',host='www.kansei.se'){
  const context=await browser.newContext({viewport:{width:320,height:850}});
  const google=[];
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());
   if(u.hostname==='www.googletagmanager.com'){google.push(u.href);return route.fulfill({contentType:'application/javascript',body:'/* intercepted for testing */'});}
   if(u.hostname===host){
    if(u.pathname.startsWith('/assets/'))return route.fulfill({contentType:u.pathname.endsWith('.js')?'application/javascript':'text/css',body:fs.readFileSync(path.join(root,u.pathname))});
    return route.fulfill({contentType:'text/html',body:fixture(id)});
   }
   return route.abort();
  });
  const page=await context.newPage();
  await page.goto('https://'+host+'/?patient=secret#private',{referer:'https://chatgpt.com/share/private?patient=secret'});
  return {context,page,google};
 }
 const {context,page,google}=await setup();
 assert.equal(google.length,0);assert.equal(await page.evaluate(()=>document.cookie),'');
 assert.equal(await page.evaluate(()=>localStorage.length),0);
 await page.locator('[data-statistics="no"]').click();
 await page.reload();assert.equal(google.length,0);assert(await page.locator('.kansei-statistics').isHidden());
 await page.locator('.kansei-statistics-settings').click();
 await page.locator('[data-statistics="yes"]').click();
 await page.waitForFunction(()=>document.querySelector('script[src*="googletagmanager"]'));
 await page.waitForLoadState('networkidle');assert.equal(google.length,1);
 const emit=()=>document.dispatchEvent(new CustomEvent('kansei:booking-intent',{detail:{event:'booking_click',placement:'header',service:'private',patient:'secret',audience:'clinician'}}));
 await page.evaluate(emit);
 let events=await page.evaluate(()=>dataLayer.map(x=>Array.from(x)));
 assert.equal(events.filter(e=>e[0]==='event'&&e[1]==='page_view').length,1);
 assert.equal(events.filter(e=>e[0]==='event'&&e[1]==='booking_click').length,1);
 assert(!JSON.stringify(events).includes('secret'));
 assert(!JSON.stringify(events).includes('private'));
 assert(!JSON.stringify(events).includes('clinician'));
 assert(events.find(e=>e[1]==='page_view')[2].page_referrer==='https://chatgpt.com/');
 await page.evaluate(()=>{document.cookie='_ga=test; Path=/; Secure';document.cookie='_ga_TEST123456=test; Domain=kansei.se; Path=/; Secure';});
 await page.locator('.kansei-statistics-settings').click();
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:850});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  const buttons=await page.locator('.kansei-statistics-actions button').evaluateAll(bs=>bs.map(b=>b.getBoundingClientRect().height));
  assert(buttons.every(h=>h>=48));
 }
 await page.locator('[data-statistics="no"]').click();
 const n=events.length;await page.evaluate(emit);
 assert.equal(await page.evaluate(()=>dataLayer.length),n);
 assert.equal(await page.evaluate(()=>window.KanseiMeasure),false);
 assert.equal(await page.evaluate(()=>document.cookie),'');
 await page.reload();assert.equal(google.length,1);
 await context.close();
 for(const [id,host] of [['','www.kansei.se'],['417935074','www.kansei.se'],['G-TEST123456','preview.invalid']]){
  const s=await setup(id,host);assert.equal(s.google.length,0);assert.equal(await s.page.locator('.kansei-statistics').count(),0);await s.context.close();
 }
 const blocked=await setup();
 await blocked.page.evaluate(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('disabled');}}));
 await blocked.page.locator('[data-statistics="yes"]').click();
 assert.equal(await blocked.page.evaluate(()=>window.KanseiMeasure),true);
 await blocked.context.close();
 await browser.close();
 console.log('PASS consent/rejection/reload/withdrawal/cookie cleanup; clean explicit payloads; missing-ID and preview fail-closed; blocked storage; 320/390/1440 layout.');
})().catch(e=>{console.error(e);process.exit(1);});
