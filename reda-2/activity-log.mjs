import {patientHistory} from './patient-history.mjs?v=20260918-1';
const labels={all:'Alla händelser',plans:'Planer',training:'Träning',feedback:'Återkoppling',contact:'Kontakt',finance:'Ekonomi',ei:'EI & beslut'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function mountActivityLog(host,{api,patientId,clinician=false,patientName="",historyContext={}}){
 let alive=true,ticket=0,cursor=null,rows=[];
 host.innerHTML=`<section class="activity-log ${clinician?'':'patient-history'}"><h2>${clinician?'Aktivitetslogg':'Min historik'}</h2>${patientName?`<p><strong>${esc(patientName)}</strong></p>`:""}<p>${clinician?'Registrerade händelser, nyast först. Datum och tid visas i svensk tid.':'Dina pass, ändringar i planen och kontakten med kliniken. Ett pass samlas i en post.'}</p>${clinician?'':'<div class="history-chips" aria-label="Visa i historiken"><button type="button" data-history="all" aria-pressed="true">Allt</button><button type="button" data-history="training" aria-pressed="false">Träning</button><button type="button" data-history="plans" aria-pressed="false">Planer</button><button type="button" data-history="contact" aria-pressed="false">Kontakt</button></div><details class="history-filter-details"><summary>Fler filter och datum</summary>'}<form class="activity-filters"><label>Visa<select name="category">${Object.entries(labels).filter(([k])=>clinician||k!=='ei').map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>Från<input type="date" name="from"></label><label>Till<input type="date" name="to"></label><button class="btn ghost" type="submit">Visa / uppdatera</button></form>${clinician?'':'</details>'}<p class="activity-status" role="status"></p><ol class="activity-events"></ol><button class="btn ghost activity-more" hidden>Visa äldre</button></section>`;
 const q=s=>host.querySelector(s),form=q('form'),status=q('.activity-status'),list=q('ol'),more=q('.activity-more');
 let filter=null;
 async function fetchPage(append=false){
  const n=++ticket;
  if(!append){filter={category:form.elements.category.value,from:form.elements.from.value||null,to:form.elements.to.value||null};rows=[];cursor=null;more.hidden=true;list.replaceChildren()}
  if(filter.from&&filter.to&&filter.from>filter.to){status.textContent='Från-datum måste vara före eller samma dag som till-datum.';more.hidden=true;return}
  status.textContent='Hämtar händelser…';more.disabled=true;
  try{
   const data=await api.activityLog(patientId,{...filter,cursor,clinician});
   if(!alive||n!==ticket||!host.isConnected)return;
   rows=append?[...rows,...data.events]:data.events;cursor=data.next_cursor;
   const visible=clinician?rows:patientHistory(rows,typeof historyContext==='function'?historyContext():historyContext);
   list.innerHTML=visible.map(e=>`<li><time datetime="${esc(e.occurred_at)}">${esc(new Date(e.occurred_at).toLocaleString('sv-SE',{timeZone:'Europe/Stockholm',dateStyle:'medium',timeStyle:'short'}))}</time><div><strong>${esc(e.title)}</strong><p>${esc(e.detail)}${e.plan_version?' · Plan v'+esc(e.plan_version):''}</p><small>${esc(labels[e.category]||e.category)}</small></div></li>`).join('');
   status.textContent=filter.category==='finance'&&!data.billing_connected?'Betalningar och abonnemang är inte anslutna. Inga ekonomihändelser registreras ännu.':rows.length?`${visible.length} ${clinician?'händelser':'poster'} visas.`:'Inga registrerade händelser för de här filtren.';
   more.hidden=!cursor;
  }catch{if(alive&&n===ticket)status.textContent='Historiken kunde inte hämtas. Försök igen med Visa / uppdatera.'}
  finally{if(alive&&n===ticket)more.disabled=false}
 }
 const setChips=()=>host.querySelectorAll('[data-history]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.history===form.elements.category.value)));
 host.querySelectorAll('[data-history]').forEach(b=>b.onclick=()=>{form.elements.category.value=b.dataset.history;setChips();fetchPage()});
 form.onsubmit=e=>{e.preventDefault();setChips();fetchPage()};more.onclick=()=>fetchPage(true);fetchPage();
 return {destroy(){alive=false;++ticket;host.replaceChildren()},refresh:()=>fetchPage()};
}
export function openActivityLog(options){
 const dialog=document.createElement('dialog');dialog.className='activity-dialog';dialog.innerHTML='<button class="btn ghost activity-close" autofocus>Stäng</button><div></div>';document.body.append(dialog);
 const view=mountActivityLog(dialog.querySelector('div'),options);const close=()=>{view.destroy();dialog.remove()};dialog.querySelector('button').onclick=()=>dialog.close();dialog.addEventListener('close',close,{once:true});dialog.showModal();return {destroy:close};
}
