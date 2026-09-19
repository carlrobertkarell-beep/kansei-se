const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function mountClinicalMandate(host,{api,onBusy}){
 let alive=true,busy=false,blocked=false,ticket=0,pending=null;
 const valid=n=>alive&&ticket===n&&host.isConnected;
 const controls=()=>{const f=host.querySelector('fieldset');if(f)f.disabled=blocked||busy||f.dataset.manage!=='true'};
 async function load(message=''){
  const n=++ticket;host.innerHTML='<p role="status">Hämtar kliniskt mandat…</p>';
  try{
   const d=await api.clinicalEISettings();if(!valid(n))return;
   const status=!d.execution_open?'Automatisk progression stängd':d.enabled?'Klinikens mandat är på':'Klinikens mandat är av';
   host.innerHTML=`<span class="ei-status">${esc(status)}</span><h3>Kliniskt mandat</h3><p>${!d.execution_open?'Du kan förbereda klinikens mandat. Den centrala körningen är stängd, så inga planer ändras automatiskt.':'Varje patient behöver en separat, granskad progressionsram innan EI får gå vidare.'}</p><form><fieldset data-manage="${!!d.can_manage}" style="border:0;padding:0;margin:0"><legend class="sr-only">Klinikens tillstånd för progression</legend><label class="team-check"><input type="checkbox" name="clinicalEnabled" ${d.enabled?'checked':''}>Tillåt progression inom godkända patientramar</label><label class="field">Högst antal automatiska steg per godkänd ram<select name="clinicalSteps">${Array.from({length:11},(_,i)=>`<option value="${i+1}" ${d.max_steps===i+1?'selected':''}>${i+1} steg</option>`).join('')}</select></label>${d.can_manage?'<button class="btn primary" type="submit">Spara kliniskt mandat</button>':''}</fieldset></form>${d.can_manage?'':'<p>Endast arbetsytans ägare med behandlarbehörighet kan ändra mandatet.</p>'}<p class="sub">När gränsen nås behövs en ny klinisk granskning. Ändringar av mandatet kräver nya godkännanden för automatiska patientramar. En återaktivering återställer inte gamla godkännanden.</p><p class="sub">Mandatversion ${Number(d.revision)}${d.updated_at?' · Sparat '+esc(new Date(d.updated_at).toLocaleString('sv-SE')):''}</p><p data-clinical-status role="status" aria-live="polite">${esc(message)}</p>`;
   const form=host.querySelector('form'),enabled=form.elements.clinicalEnabled,steps=form.elements.clinicalSteps,save=form.querySelector('button'),notice=host.querySelector('[data-clinical-status]');
   const changed=()=>enabled.checked!==!!d.enabled||Number(steps.value)!==d.max_steps;
   const refresh=()=>{controls();if(save)save.disabled=!changed()||busy||blocked};
   form.onchange=refresh;refresh();
   form.onsubmit=async e=>{
    e.preventDefault();if(busy||blocked||!d.can_manage||!changed())return;
    const value=enabled.checked,limit=Number(steps.value),signature=JSON.stringify([d.revision,value,limit]);
    if(pending?.signature!==signature)pending={signature,id:crypto.randomUUID()};
    busy=true;onBusy?.(true);refresh();notice.textContent='Sparar kliniskt mandat…';
    try{
     await api.saveClinicalEIMandate(pending.id,d.revision,value,limit);if(!valid(n))return;
     pending=null;await load('Kliniskt mandat sparat.');
    }catch(e){
     if(!valid(n))return;
     if(e.code==='40001'||e.code==='42501'){pending=null;await load((e.message||'Behörigheten har ändrats.')+' Kontrollera aktuella inställningar.');}
     else{notice.textContent=e.message||'Mandatet kunde inte sparas. Försök igen.';notice.setAttribute('role','alert')}
    }finally{busy=false;onBusy?.(false);controls();if(valid(n))refresh()}
   };
  }catch{
   if(valid(n)){host.innerHTML='<h3>Kliniskt mandat</h3><p role="alert">Det kliniska mandatet kunde inte hämtas.</p><button type="button" class="btn ghost">Försök igen</button>';host.querySelector('button').onclick=()=>load()}
  }
 }
 load();return {destroy(){alive=false;++ticket;host.replaceChildren()},setBlocked(value){blocked=value;host.inert=value;controls()}};
}
