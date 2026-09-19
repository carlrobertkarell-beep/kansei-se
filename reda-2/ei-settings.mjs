const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function mountEISettings(host,{api,onBusy,onImport}){
 if(!host||!api.eiSettings)return null;
 let alive=true,busy=false,ticket=0,pending=null;
 const valid=n=>alive&&n===ticket&&host.isConnected;
 async function load(message=''){
  if(busy||!alive)return;
  const n=++ticket;host.innerHTML='<p role="status">Hämtar EI:s mandat…</p>';
  try{
   const d=await api.eiSettings();if(!valid(n))return;
   host.innerHTML=`<section class="ei-mandate-card" aria-labelledby="followupMandateTitle"><span class="ei-status">${d.auto_followup?'Automatisk uppföljning på':'Automatisk uppföljning av'}</span><h3 id="followupMandateTitle">Uppföljningsuppgifter</h3><p>Bestäm om EI ska skapa en uppgift åt behandlaren när en patient rapporterar något som behöver följas upp.</p><form><label class="team-check"><input type="checkbox" name="automatic" ${d.auto_followup?'checked':''} ${d.can_manage?'':'disabled'}>Skapa uppföljningsuppgifter automatiskt vid nya patientsignaler</label><p>Uppgifterna samlas per patient. Patientsignalerna syns även när detta är avstängt. Mandatet skickar inga meddelanden och ändrar inte patientens plan.</p>${d.can_manage?'<button class="btn primary" type="submit">Spara mandat</button>':'<p>Endast arbetsytans ägare kan ändra mandatet.</p>'}</form><p data-ei-status role="status" aria-live="polite">${esc(message)}</p></section><section class="ei-mandate-card" aria-labelledby="clinicalMandateTitle"><h3 id="clinicalMandateTitle">Patientens behandling</h3><p>Administrativ uppföljning och ändringar i behandlingen har separata befogenheter.</p><ul class="ei-permissions"><li><strong>Förbereda EI-förslag</strong><span>Underlag för din granskning</span></li><li><strong>Skicka meddelande i Reda</strong><span>Ditt godkännande krävs</span></li><li><strong>Ändra klinisk plan</strong><span>${d.clinical_progression_enabled?'Separat godkänd patientram krävs':'Automatisk progression stängd'}</span></li><li><strong>Extern AI med patientuppgifter</strong><span>${d.external_ai_enabled?'Separat styrning':'Stängd'}</span></li></ul></section><details class="team-panel ei-connections"><summary>Anslutningar och import</summary><p>Bokning, journalöverföring och abonnemang kräver en verifierad anslutning till respektive system.</p>${(d.connections||[]).map(c=>'<p><strong>'+esc(c.name)+'</strong> · '+(c.connected?'Ansluten':'Inte ansluten')+'</p>').join('')}<button type="button" class="btn ghost" data-import-patient>Importera patient från fil</button><p class="sub">Du granskar patientuppgifterna före sparning.</p>${d.imports?.length?'<details><summary>Sparade uppgifter från externa källor</summary>'+d.imports.map(x=>'<p>'+esc(x.source)+': '+Number(x.patients)+' av dina patienter. Senast sparat '+esc(new Date(x.last_saved).toLocaleDateString('sv-SE'))+'.</p>').join('')+'</details>':''}</details>`;
   const q=s=>host.querySelector(s);q('[data-import-patient]').onclick=onImport;
   const form=q('form'),checkbox=q('[name="automatic"]'),save=form.querySelector('button');
   if(save){save.disabled=true;checkbox.onchange=()=>{save.disabled=checkbox.checked===!!d.auto_followup}}
   form.onsubmit=async e=>{
    e.preventDefault();if(busy||!d.can_manage||checkbox.checked===!!d.auto_followup)return;
    const value=checkbox.checked,signature=JSON.stringify([d.revision,value]);
    if(pending?.signature!==signature)pending={signature,id:crypto.randomUUID()};
    busy=true;onBusy?.(true);host.querySelectorAll('button,input').forEach(el=>el.disabled=true);
    q('[data-ei-status]').textContent='Sparar mandatet…';
    try{
     await api.saveEIMandate(pending.id,d.revision,value);if(!valid(n))return;
     pending=null;busy=false;await load('Mandatet är sparat.');
    }catch(e){
     if(valid(n)){
      q('[data-ei-status]').textContent=e.message||'Mandatet kunde inte sparas. Försök igen.';
      q('[data-ei-status]').setAttribute('role','alert');
      if(e.code==='40001'){pending=null;busy=false;await load(e.message+' Kontrollera det aktuella mandatet innan du ändrar det igen.')}
     }
    }finally{
     busy=false;onBusy?.(false);
     // Never re-enable another revision's or another role's controls after a reload.
     if(valid(n)){checkbox.disabled=!d.can_manage;save.disabled=checkbox.checked===!!d.auto_followup;q('[data-import-patient]').disabled=false}
    }
   };
  }catch{
   if(valid(n)){host.innerHTML='<section class="ei-mandate-card"><p role="alert">EI:s mandat kunde inte hämtas. Försök igen.</p><button type="button" class="btn ghost" data-retry-mandate>Försök igen</button></section>';host.querySelector('button').onclick=()=>load()}
  }
 }
 load();return {destroy(){alive=false;++ticket;host.replaceChildren()},isBusy:()=>busy};
}
