import {decisionLabels} from './runtime-ui.mjs?v=20260919-mandate1';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function previewGroup(d){if(d?.code==='no_frame')return 'uncovered';if(d?.action==='advance'&&d.code==='ready')return 'ready';if(['wait','hold'].includes(d?.action))return 'waiting';return 'review'}
const groups={review:'Behöver din bedömning',ready:'Kan gå vidare',waiting:'Avvaktar',uncovered:'Saknar godkänd ram'};
const nextAction=d=>({ready:'Nästa steg finns i den godkända ramen.',pending_review:'Öppna patienten och bedöm återkopplingen.',expired:'Granska ramens giltighet och nästa upplägg.',version:'Kontrollera aktuell plan och godkänd ram.',mandate_limit:'Gör en ny klinisk granskning före fler steg.',mandate_changed:'Granska patientramen mot det aktuella mandatet.',mandate_disabled:'Kontrollera klinikens mandat.',clinician_authority:'Kontrollera vem som ansvarar för patienten.',complete:'Bedöm om ramen kan avslutas eller behöver ersättas.',no_frame:'Förbered och granska en ram för att kunna provköra progression.'}[d?.code]||(['wait','hold'].includes(d?.action)?'Avvakta enligt den aktuella planen och följ återkopplingen.':'Öppna patientens underlag för bedömning.'));
export function mountShadowFleet(host,{api,onOpen}){
 if(!host||!api.previewProgressionBatch)return null;
 let alive=true,running=false,generation=0,rows=[],group='review',search='',page=0,message='Ingen provkörning gjord i den här arbetsytan.',complete=false;
 host.innerHTML=`<section class="shadow-fleet" aria-labelledby="shadowFleetTitle"><div class="shadow-heading"><div><span class="ei-status">Provkörning · inga planändringar</span><h3 id="shadowFleetTitle">Vad kan EI avlasta dig med?</h3><p>Pröva dina tilldelade patienters aktiva planer mot motorns villkor. Du får en överblick och kan öppna de patienter som behöver dig.</p></div><button class="btn primary" type="button" data-preview-run>Provkör aktiva planer</button></div><p data-preview-status role="status" aria-live="polite"></p><p class="sub">Resultaten är ögonblicksbilder, inte ett godkännande för automatisk behandling. Ordinationer, sparade beslut och ärenden ändras inte.</p><div data-preview-results hidden><div class="shadow-groups" aria-label="Resultatgrupper"></div><p data-preview-coverage class="sub"></p><label class="shadow-search">Sök i provkörningen<input type="search" data-preview-search placeholder="Patientens namn"></label><div data-preview-list></div><div class="shadow-pagination"><button type="button" class="btn ghost" data-preview-prev>Föregående</button><span data-preview-page></span><button type="button" class="btn ghost" data-preview-next>Nästa</button></div></div></section>`;
 const expanded=new Set();
 const q=s=>host.querySelector(s),valid=n=>alive&&generation===n&&host.isConnected;
 function render(){
  if(!alive)return;
  host.querySelectorAll('[data-preview-evidence]').forEach(el=>el.open?expanded.add(el.dataset.previewEvidence):expanded.delete(el.dataset.previewEvidence));
  q('[data-preview-status]').textContent=message;
  q('[data-preview-run]').textContent=running?'Avbryt provkörning':rows.length?'Provkör på nytt':'Provkör aktiva planer';
  q('[data-preview-results]').hidden=!rows.length;
  const counts=Object.fromEntries(Object.keys(groups).map(k=>[k,rows.filter(r=>previewGroup(r.decision)===k).length]));
  q('.shadow-groups').innerHTML=['review','ready','waiting'].map(k=>`<button type="button" data-preview-group="${k}" aria-pressed="${group===k}"><strong>${counts[k]}</strong><span>${groups[k]}</span></button>`).join('');
  q('[data-preview-coverage]').innerHTML=`${rows.length-counts.uncovered} av ${rows.length} genomgångna planer har en godkänd ram.${counts.uncovered?` <button class="btn text-btn" type="button" data-preview-group="uncovered" aria-pressed="${group==='uncovered'}">${counts.uncovered} saknar godkänd ram</button>`:''}${complete?'':' Körningen är ännu inte fullständig.'}`;
  const filtered=rows.filter(r=>previewGroup(r.decision)===group&&r.display_name.toLocaleLowerCase('sv').includes(search.toLocaleLowerCase('sv')));
  page=Math.min(page,Math.max(0,Math.ceil(filtered.length/25)-1));
  q('[data-preview-list]').innerHTML=`<h4>${groups[group]}</h4>`+(filtered.length?filtered.slice(page*25,page*25+25).map(r=>{const d=r.decision,m=d.metrics||{};return `<article class="shadow-row"><div><h5>${esc(r.display_name)}</h5><p>${esc(decisionLabels[d.code]||'Beslutet behöver kontrolleras.')}</p><p class="shadow-action">${esc(nextAction(d))}</p><details data-preview-evidence="${esc(r.patient_id)}" ${expanded.has(r.patient_id)?'open':''}><summary>Beslutsunderlag</summary><p>Provkört ${esc(new Date(r.evaluated_at).toLocaleString('sv-SE'))}.</p>${d.frame_id?`<p>Steg ${Number(d.step)+1} av ${Number(d.steps)} · ${d.execution==='automatic'?'Automatisk ram':'Granskningsläge'}</p>${['ready','evidence','time','complete','mandate_limit'].includes(d.code)?`<dl><dt>Uppföljda träningsdagar</dt><dd>${Number(m.successfulDays||0)} av ${Number(m.requiredDays||0)}</dd><dt>Dagar på aktuell nivå</dt><dd>${Number(m.daysAtStep||0)}</dd></dl>`:'<p>Prövningen av träningsunderlaget avbröts vid orsaken ovan.</p>'}${d.next_step?'<p>Nästa steg: '+esc(d.next_step)+'</p>':''}<p>${d.execution_open?'Central körning öppen.':'Automatisk progression är stängd.'} ${d.mandate_enabled?'Klinikens mandat är på.':'Klinikens mandat är av.'} Provkörningen tillämpar inga ändringar.</p>`:''}<p class="sub">Nya pass, svar och planändringar kan ändra utfallet. Öppna patienten för aktuellt underlag.</p></details></div><button class="btn ghost" type="button" data-preview-open="${esc(r.patient_id)}">Öppna patient</button></article>`}).join(''):'<p class="shadow-empty">'+(search?'Ingen patient matchar sökningen.':'Inga genomgångna planer i den här gruppen.')+'</p>');
  q('[data-preview-page]').textContent=filtered.length?`${page*25+1}–${Math.min((page+1)*25,filtered.length)} av ${filtered.length}`:'0 patienter';
  q('[data-preview-prev]').disabled=page===0;q('[data-preview-next]').disabled=(page+1)*25>=filtered.length;
 }
 async function run(){
  if(running){running=false;++generation;complete=false;message=`Avbruten. ${rows.length} planer genomgångna. Resultatet är ofullständigt.`;render();return}
  running=true;complete=false;rows=[];expanded.clear();q('[data-preview-list]').replaceChildren();page=0;group='review';search='';q('[data-preview-search]').value='';const n=++generation;let cursor=null;const seen=new Set(),cursors=new Set();message='Provkör dina aktiva planer…';render();
  try{
   do{
    const data=await api.previewProgressionBatch(cursor);if(!valid(n))return;
    if(data?.preview!==true||!Array.isArray(data.items))throw Error('Svaret från provkörningen kunde inte kontrolleras.');
    for(const row of data.items){if(!row.patient_id||typeof row.display_name!=='string'||!row.decision||row.decision.applied!==false)throw Error('Svaret från provkörningen kunde inte kontrolleras.');if(!seen.has(row.patient_id)){seen.add(row.patient_id);rows.push(row)}}
    cursor=data.next_cursor||null;
    if(cursor&&cursors.has(cursor))throw Error('Provkörningen fastnade. Starta en ny körning.');
    if(cursor)cursors.add(cursor);
    message=`${rows.length} planer genomgångna. Provkörningen pågår…`;render();
   }while(cursor);
   running=false;complete=true;message=rows.length?`Provkörning klar. ${rows.length} aktiva planer genomgångna. Resultat från ${new Date().toLocaleTimeString('sv-SE',{hour:'2-digit',minute:'2-digit'})}.`:'Inga tilldelade patienter med aktiva planer att provköra.';
   if(!rows.some(r=>previewGroup(r.decision)===group))group=['review','ready','waiting','uncovered'].find(k=>rows.some(r=>previewGroup(r.decision)===k))||'review';
   render();
  }catch(e){if(valid(n)){running=false;complete=false;if(e.code==='42501'||e.code==='PGRST301'){rows=[];message='Åtkomsten kunde inte verifieras. Uppdatera arbetsytans åtkomst.'}else message=`Provkörningen kunde inte slutföras. ${rows.length} planer genomgångna. Starta en ny körning för en fullständig överblick.`;render();q('[data-preview-status]').setAttribute('role','alert')}}
 }
 q('[data-preview-run]').onclick=()=>{q('[data-preview-status]').setAttribute('role','status');run()};
 q('[data-preview-search]').oninput=e=>{search=e.target.value;page=0;render()};
 q('[data-preview-prev]').onclick=()=>{page--;render()};q('[data-preview-next]').onclick=()=>{page++;render()};
 const click=async e=>{const filter=e.target.closest('[data-preview-group]');if(filter){group=filter.dataset.previewGroup;page=0;render();host.querySelector('[data-preview-group="'+group+'"]')?.focus()}const open=e.target.closest('[data-preview-open]');if(open){open.disabled=true;try{await onOpen?.(open.dataset.previewOpen)}catch{message='Patientens aktuella underlag kunde inte öppnas. Försök igen.';render()}finally{if(alive&&open.isConnected)open.disabled=false}}};
 host.addEventListener('click',click);
 render();return {destroy(){alive=false;++generation;rows=[];host.removeEventListener('click',click);host.replaceChildren()}};
}
