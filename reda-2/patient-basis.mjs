const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=s=>s?new Date(s).toLocaleDateString('sv-SE',{timeZone:'Europe/Stockholm'}):'Datum saknas';
export function basisReadiness(b,today=new Date().toISOString().slice(0,10)){
 const gaps=[],p=b?.profile||{},plan=b?.plan,report=b?.latest;
 if(!p.focus)gaps.push({label:'Behandlingsfokus saknas',target:'profile'});
 if(!plan?.goal&&!p.goal)gaps.push({label:'Patientens mål saknas',target:'profile'});
 if(!plan)gaps.push({label:'Aktiv plan saknas',target:'plan'});
 if(plan&&!report)gaps.push({label:'Patientens egen målskattning och förutsättningar saknas',target:'report'});
 if(report&&Date.parse(today+'T23:59:59Z')-Date.parse(report.created_at)>30*86400000)gaps.push({label:'Patientens uppgifter är äldre än 30 dagar',target:'report'});
 if(plan&&p.goal&&p.goal!==plan.goal)gaps.push({label:'Målet i patientprofilen skiljer sig från den aktiva planen',target:'profile'});
 return gaps;
}
export function goalChange(b){if(!b?.latest||!b?.baseline||b.latest.goal_key!==b.baseline.goal_key)return null;return b.latest.answers.ability-b.baseline.answers.ability}
export function checkinSummary(r){return r?`Målskattning ${r.answers.ability}/10 · ${r.answers.minutes} minuter · ${r.answers.equipment==='gym'?'Gym':'Hemma'} · ${r.answers.band?'Har band':'Utan band'} · ${r.answers.floorOK?'Golv fungerar':'Undviker golv'}`:''}
export function basisHTML(b,today){
 if(!b)return '';const gaps=basisReadiness(b,today),delta=goalChange(b),r=b.latest;
 return `<section class="basis-card"><div class="basis-heading"><div><p class="eyebrow">Samlad patientbild</p><h4>${gaps.length?gaps.length+' saker att komplettera eller bekräfta':'Underlag finns för nästa bedömning'}</h4></div><button class="btn ghost" type="button" data-basis-edit>Komplettera</button></div>${gaps.length?'<ul class="basis-gaps">'+gaps.map(g=>'<li>'+esc(g.label)+'</li>').join(''):'<p>Uppgifterna nedan finns sparade. Det är inte ett godkännande av en klinisk förändring.</p>'}<dl class="basis-sources"><div><dt>Behandlarens utgångspunkt</dt><dd>${esc(b.profile?.focus||'Ej angivet')} · ${esc(b.profile?.goal||'Mål ej angivet')}<small>Patientprofil · ${date(b.profile?.updated_at)}</small></dd></div><div><dt>Aktiv ordination</dt><dd>${esc(b.plan?.goal||'Ingen aktiv plan')}<small>${b.plan?'Plan v'+esc(b.plan.version)+' · '+date(b.plan.activated_at):'Plan behöver förberedas'}</small></dd></div><div><dt>Patientens egna uppgifter</dt><dd>${r?esc(checkinSummary(r)):'Inga uppgifter för det aktuella målet ännu'}<small>${r?'Patientens svar · '+date(r.created_at)+' · plan v'+esc(r.plan_version):'Patienten kan svara under Mitt mål och min vardag'}</small></dd></div></dl>${r?'<p><strong>Målskattning: '+esc(r.answers.ability)+'/10</strong>'+(b.baseline.id!==r.id?' · '+(delta>0?'+':'')+esc(delta)+' från första skattningen':' · Första skattningen')+'</p><p class="sub">Patientens egen skattning, 0 = inte alls och 10 = utan problem. Jämförelsen gäller samma mål och behandlingsfokus.</p>':''}</section>`;
}
export function mountPatientCheckin(host,{api,patientId,onSaved,onBusy}){
 if(!host||!api.myCheckins)return null;
 let alive=true,ticket=0,busy=false,data=null,pending=null;
 host.innerHTML='<details class="card basis-card"><summary>Mitt mål och min vardag</summary><p data-checkin-status role="status"></p><div data-checkin-body></div><button class="btn ghost" type="button" data-checkin-refresh>Uppdatera</button></details>';
 const q=s=>host.querySelector(s),status=t=>{if(alive)q('[data-checkin-status]').textContent=t};
 async function refresh(){if(busy)return;const n=++ticket;status('Hämtar ditt mål…');
  try{const r=await api.myCheckins(patientId);if(!alive||n!==ticket||!host.isConnected)return;data=r;pending=null;render();status('')}
  catch{if(alive&&n===ticket){data=null;q('[data-checkin-body]').replaceChildren();status('Ditt mål kunde inte hämtas. Försök med Uppdatera.')}}
 }
 function render(){const p=data.plan,r=data.latest,a=r?.answers||{};
  if(!p?.goal){q('[data-checkin-body]').textContent='Din behandlare behöver ange ett mål i den aktiva planen innan du kan följa det här.';return}
  q('[data-checkin-body]').innerHTML=`<p><strong>${esc(p.goal)}</strong></p><p>Hur fungerar målet och träningen i din vardag? Dina svar hjälper behandlaren att följa upp planen.</p>${r?'<p>Senast '+date(r.created_at)+': '+esc(a.ability)+'/10 · första skattningen '+esc(data.baseline.answers.ability)+'/10.</p>':'<p>Din första skattning blir utgångspunkt för kommande uppföljningar.</p>'}<form class="basis-form"><label>Hur väl klarar du målet idag?<select name="ability" required><option value="">Välj 0–10</option>${Array.from({length:11},(_,i)=>'<option value="'+i+'">'+i+(i===0?' · Inte alls':i===10?' · Utan problem':'')+'</option>').join('')}</select></label><label>Tid som brukar fungera för ett pass<select name="minutes" required><option value="">Välj tid</option>${[5,10,15,20,30,45,60].map(n=>'<option value="'+n+'">'+n+' minuter</option>').join('')}</select></label><label>Var tränar du främst?<select name="equipment" required><option value="">Välj plats</option><option value="home">Hemma</option><option value="gym">Gym</option></select></label><label>Har du träningsband?<select name="band" required><option value="">Välj</option><option value="true">Ja</option><option value="false">Nej</option></select></label><label>Fungerar det att komma ner på och upp från golvet?<select name="floorOK" required><option value="">Välj</option><option value="true">Ja</option><option value="false">Nej, jag behöver annat upplägg</option></select></label><button class="btn primary" type="submit">Spara min uppföljning</button></form><p class="sub">Din egen skattning ändrar inte ordinationen automatiskt. Fortsätt följa den aktuella planen.</p>`;
  const form=q('form');for(const k of ['minutes','equipment','band','floorOK'])if(a[k]!==undefined)form.elements[k].value=String(a[k]);
  form.onsubmit=async e=>{e.preventDefault();if(busy||!alive)return;const answers={ability:Number(form.elements.ability.value),minutes:Number(form.elements.minutes.value),equipment:form.elements.equipment.value,band:form.elements.band.value==='true',floorOK:form.elements.floorOK.value==='true'},signature=JSON.stringify([p.id,answers]);if(pending?.signature!==signature)pending={signature,id:crypto.randomUUID()};busy=true;onBusy?.(true);++ticket;host.querySelectorAll('button,select').forEach(e=>e.disabled=true);status('Sparar dina uppgifter…');
   try{await api.submitCheckin(p.id,pending.id,answers);if(!alive)return;pending=null;busy=false;await refresh();status('Din uppföljning är sparad till kliniken.');onSaved?.()}
   catch(e){if(alive)status(e.message||'Uppgifterna kunde inte sparas. Dina val är kvar. Försök igen.')}
   finally{busy=false;onBusy?.(false);if(alive)host.querySelectorAll('button,select').forEach(e=>e.disabled=false)}
  };
 }
 q('[data-checkin-refresh]').onclick=refresh;refresh();return {refresh,isBusy:()=>busy,destroy(){alive=false;++ticket;host.replaceChildren()}};
}
