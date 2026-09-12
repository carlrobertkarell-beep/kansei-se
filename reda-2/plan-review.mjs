import {adaptationOptions,prescriptionFacts} from './everyday-support.mjs?v=1';
import {cleanProgression} from './plan-authoring-model.mjs?v=2';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function careText(plan,Care=globalThis.RedaCare){
 if(!Care)return plan?.reviewDate||'Enligt överenskommen uppföljning';
 const c=Care.overview(plan||{});
 return [c.label,c.weeks?c.weeks+' veckor':'',c.startDate?'Start '+c.startDate:'',...c.points.map(x=>x.label+': '+x.date+' · '+x.contact)].filter(Boolean).join(' · ');
}
export function planCandidates(detail,base,P,D){
 if(!base||detail.cases?.some(c=>c.code==='changed_symptoms'))return [];
 const f=detail.frame,decision=detail.decision;
 if(decision?.action==='advance'&&!decision.applied&&!(detail.cases||[]).some(c=>c.status!=='resolved')&&!detail.patient?.pending_messages&&f?.policy?.steps?.[f.current_step+1]){
  const step=f.policy.steps[f.current_step+1];
  return [{id:'next-step',title:step.label,detail:step.rationale||'Nästa förberedda steg i den godkända ramen. EI har prövat patientens sparade underlag.',decisionId:decision.id,plan:cleanProgression({...structuredClone(base),...structuredClone(step.plan)})}];
 }
 const c=detail.cases?.find(c=>c.status!=='resolved'&&((c.reflection?.plan_id===detail.patient.plan_id&&['time','equipment'].includes(c.reflection.answers?.barrier))||(c.checkin?.plan_id===detail.patient.plan_id&&['training_barrier','changed_environment'].includes(c.code))));
 if(!c)return [];
 const barrier=c.reflection?.answers?.barrier||(c.code==='training_barrier'?'time':'equipment');
 let choices=adaptationOptions(P,D,base,barrier);
 if(c.checkin)choices=choices.filter(x=>x.id==='less-rounds'||(x.id==='band'&&!c.checkin.answers.band)||(x.id==='floor'&&!c.checkin.answers.floorOK)||(x.id==='home'&&c.checkin.answers.equipment==='home'));
 return choices.map(x=>{const plan=cleanProgression(x.plan);delete plan.planOptions;return {...x,plan,detail:x.detail+' Förslaget utgår från patientens sparade svar för den aktuella planen. Tidigare vardagsalternativ behöver granskas på nytt.'}});
}
export function changeRows(before,after){
 const old=new Map((before?.exercises||[]).map(x=>[x.id,x])),next=new Map((after?.exercises||[]).map(x=>[x.id,x]));
 const rows=[];
 for(const id of new Set([...old.keys(),...next.keys()])){
  const a=old.get(id),b=next.get(id);
  if(!a||!b){rows.push({name:(b||a).name,label:'Övning',before:a?'Ingår':'Ingår inte',after:b?'Ingår':'Tas bort'});continue}
  const aa=new Map(prescriptionFacts(a)),bb=new Map(prescriptionFacts(b));
  for(const label of new Set([...aa.keys(),...bb.keys()]))if(aa.get(label)!==bb.get(label))rows.push({name:b.name,label,before:aa.get(label)||'Inte angivet',after:bb.get(label)||'Inte angivet'});
  if(JSON.stringify(a.instructions)!==JSON.stringify(b.instructions))rows.push({name:b.name,label:'Instruktion',before:(a.instructions||[]).join(' '),after:(b.instructions||[]).join(' ')});
 }
 if(before&&JSON.stringify((before.exercises||[]).map(x=>x.id))!==JSON.stringify((after.exercises||[]).map(x=>x.id)))rows.push({name:'Planen',label:'Övningsordning',before:(before.exercises||[]).map(x=>x.name).join(' → '),after:(after.exercises||[]).map(x=>x.name).join(' → ')});
 if(JSON.stringify(before?.careJourney)!==JSON.stringify(after?.careJourney))rows.push({name:'Planen',label:'Uppföljningsupplägg',before:careText(before),after:careText(after)});
 for(const [key,label]of [['goal','Mål'],['clinicianNote','Individuella råd'],['reviewDate','Uppföljningsdatum']])if((before?.[key]||'')!==(after?.[key]||''))rows.push({name:'Planen',label,before:before?.[key]||'Inte angivet',after:after?.[key]||'Inte angivet'});
 if(before?.planOptions&&!after?.planOptions)rows.push({name:'Planen',label:'Vardagsalternativ',before:'Tidigare godkända alternativ',after:'Behöver granskas på nytt'});
 if(JSON.stringify(before?.schedule)!==JSON.stringify(after?.schedule))rows.push({name:'Planen',label:'Träningsdagar',before:(before?.schedule?.days||[]).join(', ')||'Inte angivet',after:(after?.schedule?.days||[]).join(', ')});
 return rows;
}
export function handoverHTML(h){if(!h)return '';const states={pending:'Inbjudan väntar på utskick',sending:'Utskick pågår eller inväntar kvitto',accepted:'Inbjudan lämnad till e-posttjänsten',failed:'Inbjudan kunde inte skickas',not_requested:'Planen finns i patientens Reda'};
 return '<section class="handover-status"><h4>Överlämning och start</h4><ol><li>✓ Plan publicerad</li><li>'+esc(states[h.delivery_state]||'Utskick behöver kontrolleras')+'</li><li>'+(h.opened_at?'✓ Planen öppnad '+esc(new Date(h.opened_at).toLocaleDateString('sv-SE')):'Patienten har inte öppnat planen ännu')+'</li><li>'+(h.first_session_at?'✓ Första passet påbörjat':'Första passet återstår')+'</li></ol>'+(['pending','failed','sending'].includes(h.delivery_state)?'<button class="btn ghost" data-retry-invitation>Försök skicka inbjudan</button>':'')+'<p data-invitation-status role="status"></p></section>';
}
export async function openPlanReview({api,patientId,payload=null,email='',onBusy,onSaved}){
 const dialog=document.createElement('dialog');dialog.className='plan-review';dialog.innerHTML='<p role="status">Hämtar aktuell plan och patientens underlag…</p>';document.body.append(dialog);dialog.showModal();
 let busy=false,alive=true,pending=null,receipt=null,chosen=null,detail,base,choices=[],savedDraftFingerprint='';
 const q=s=>dialog.querySelector(s),close=()=>{if(busy)return;alive=false;dialog.close();dialog.remove()};dialog.addEventListener('cancel',e=>{e.preventDefault();close()});
 const lock=v=>{busy=v;onBusy?.(v);dialog.querySelectorAll('button,input,select,textarea').forEach(x=>x.disabled=v)};
 function comparison(){const rows=changeRows(base,chosen.plan);q('[data-diff]').innerHTML=rows.length?'<table class="basis-table"><thead><tr><th>Ändring</th><th>Nu</th><th>Förslag</th></tr></thead><tbody>'+rows.map(r=>'<tr><th>'+esc(r.name)+'<br>'+esc(r.label)+'</th><td>'+esc(r.before)+'</td><td>'+esc(r.after)+'</td></tr>').join('')+'</tbody></table>':'<p>Ordinationen är oförändrad.</p>';
  q('[data-exercises]').innerHTML=chosen.plan.exercises.map((x,i)=>'<details><summary>'+esc(x.name)+' · '+esc(x.dose?.label||'')+'</summary><p>'+prescriptionFacts(x).map(([k,v])=>esc(k)+': '+esc(v)).join(' · ')+'</p><ol>'+(x.instructions||[]).map(t=>'<li>'+esc(t)+'</li>').join('')+'</ol><div class="review-dose">'+[['sets','Omgångar',1,8],['reps','Repetitioner',1,100],['hold','Hålltid',0,180],['rest','Vila',0,600],['tempo','Rörelsecykel',1,60]].map(([k,l,min,max])=>'<label>'+l+'<input data-dose="'+k+'" data-index="'+i+'" type="number" min="'+min+'" max="'+max+'" value="'+x.dose[k]+'"></label>').join('')+'</div></details>').join('');
  dialog.querySelectorAll('[data-dose]').forEach(e=>e.onchange=()=>{try{chosen.plan=window.RedaPlanner.editExercise(chosen.plan,Number(e.dataset.index),{[e.dataset.dose]:Number(e.value)});delete chosen.plan.planOptions;pending=null;q('[data-reviewed]').checked=false;comparison()}catch(err){q('[data-status]').textContent=err.message}});
  const issues=[...(chosen.plan.warnings||[]),...(window.RedaIntelligence?.checks(chosen.plan)||[]),...(window.RedaCare?.issues?.(window.RedaCare.read(chosen.plan))||[])];q('[data-issues]').textContent=issues.join(' · ');q('[data-publish]').disabled=!!issues.length||!detail.delivery_enabled;q('[data-draft]').disabled=savedDraftFingerprint===JSON.stringify(chosen.plan);
 }
 function draw(){dialog.innerHTML='<header><div><p class="eyebrow">Granska och lämna över</p><h2>'+esc(detail.patient.display_name)+'</h2></div><button class="btn ghost" data-close>Stäng</button></header><p>'+esc(base?'Den aktuella planen är v'+detail.patient.plan_version+'. Du godkänner en ny version.':'Patientens första digitala plan.')+'</p>'+(choices.length>1?'<label>EI:s förslag<select data-choice>'+choices.map((c,i)=>'<option value="'+i+'">'+esc(c.title)+'</option>').join('')+'</select></label>':'')+'<h3 data-title></h3><p data-why></p><div data-diff></div><details><summary>Övningar, instruktioner och dos · justera vid behov</summary><div data-exercises></div></details><p><b>Uppföljning:</b> '+esc(careText(chosen.plan))+'</p><label>Din bedömning<textarea data-note maxlength="1000" placeholder="Kort motivering till din bedömning"></textarea></label><label>Texten patienten ser<textarea data-message maxlength="500">'+esc(base?'Din plan är uppdaterad. Se ändringarna i övningarna innan du startar nästa pass.':'Här är planen vi har förberett för dig. Börja med att läsa övningarna och starta ditt första pass när det passar enligt träningsdagarna.')+'</textarea></label>'+(!detail.patient.connected?'<label>Patientens e-postadress<input data-email type="email" required autocomplete="off" value="'+esc(email||detail.contact?.email||'')+'"></label>':'')+'<label class="review-confirm"><input type="checkbox" data-reviewed>Jag har granskat mottagare, övningar, instruktioner, sida, dos och uppföljning.</label><p data-issues role="alert"></p>'+(!detail.delivery_enabled?'<p class="notice">Patientdistribution är stängd tills klinisk granskning och e-postprov är klara. Du kan granska förslaget och spara ett utkast.</p>':'')+'<p data-status role="status"></p><footer><button class="btn ghost" data-draft>Spara som utkast</button><button class="btn primary" data-publish>Godkänn och lämna över</button></footer>';
  q('[data-close]').onclick=close;const title=()=>{q('[data-title]').textContent=chosen.title;q('[data-why]').textContent=chosen.detail;comparison()};title();q('[data-choice]')?.addEventListener('change',e=>{chosen=structuredClone(choices[Number(e.target.value)]);q('[data-reviewed]').checked=false;pending=null;title()});
  q('[data-draft]').onclick=async()=>{lock(true);try{const r=await api.createDraft(patientId,chosen.plan);q('[data-status]').textContent='Utkast v'+r.version+' sparat. Patienten ser det först efter godkänd överlämning.';savedDraftFingerprint=JSON.stringify(chosen.plan)}catch(e){q('[data-status]').textContent=e.message}finally{lock(false);comparison()}};
  q('[data-publish]').onclick=publish;for(const selector of ['[data-email]','[data-message]'])q(selector)?.addEventListener('input',()=>{q('[data-reviewed]').checked=false;pending=null});
 }
 async function publish(){
  if(busy||!q('[data-reviewed]').checked){q('[data-status]').textContent='Bekräfta att du har granskat innehållet.';return}
  const note=q('[data-note]').value.trim(),patientMessage=q('[data-message]').value.trim(),mail=q('[data-email]')?.value.trim()||null;
  if(note.length<5||patientMessage.length<5||(!detail.patient.connected&&!q('[data-email]').checkValidity())){q('[data-status]').textContent='Ange din bedömning, text till patienten och en giltig mottagaradress.';return}
  const input={patientId,token:detail.token,basePlanId:detail.patient.plan_id||null,payload:chosen.plan,note,patientMessage,email:mail,decisionId:chosen.decisionId||null},signature=JSON.stringify(input);
  if(pending?.signature!==signature)pending={id:crypto.randomUUID(),signature};lock(true);
  try{receipt=await api.publishReviewed({...input,requestId:pending.id});pending=null;
   let sent=receipt.delivery_state==='not_requested';if(!sent)try{await api.sendInvitation(receipt.id);sent=true}catch{}
   const result=receipt;dialog.innerHTML='<h2>Plan v'+esc(result.version)+' är publicerad</h2><p>'+esc(sent?(mail?'Inbjudan har lämnats till e-posttjänsten. Öppnad plan och första pass syns i patientöversikten.':'Patienten ser den nya planen vid nästa hämtning i Reda.'):'Planen är publicerad, men utskicket är inte bekräftat. Försök skicka igen från patientöversikten. Ingen ny plan behövs.')+'</p><p>Öppna patientsignaler ligger kvar tills du dokumenterar att de är bedömda.</p><button class="btn primary" data-done>Klart</button>';q('[data-done]').onclick=close;try{await onSaved?.(result)}catch{if(alive)dialog.querySelector('p').textContent+=' Överblicken kunde inte uppdateras. Stäng och hämta patienten igen; publiceringen är sparad.'};
  }catch(e){q('[data-status]').textContent=e.message||'Överlämningen kunde inte bekräftas. Försök igen med samma innehåll.';if(e.code==='40001'){q('[data-publish]').dataset.stale='true';q('[data-status]').textContent+=' Stäng och öppna granskningen igen.'}}
  finally{lock(false);if(!receipt&&alive){comparison();if(q('[data-publish]')?.dataset.stale)q('[data-publish]').disabled=true}}
 }
 try{detail=await api.dashboardPatient(patientId);if(!payload&&detail.decision?.action==='advance'&&api.evaluateProgression){await api.evaluateProgression(patientId,crypto.randomUUID());if(!alive)return;detail=await api.dashboardPatient(patientId)}const summary=await api.patientSummary(patientId);if(!alive)return;const active=summary.plans.find(p=>p.status==='active');if((active?.id||null)!==(detail.patient.plan_id||null))throw Error('Planen har ändrats. Stäng och öppna granskningen igen.');base=active?.payload||null;
  choices=payload?[{id:'manual',title:base?'Din granskade planändring':'Första planen',detail:'Granska det samlade innehållet och mottagaren före överlämning.',plan:structuredClone(payload)}]:planCandidates(detail,base,window.RedaPlanner,window.RedaData);
  if(!choices.length)throw Error('Det finns inget komplett planförslag på aktuellt underlag. Öppna hela patienten för att komplettera eller anpassa planen.');chosen=structuredClone(choices[0]);draw();
 }catch(e){if(alive){dialog.innerHTML='<h2>Granskningen kunde inte öppnas</h2><p>'+esc(e.message)+'</p><button class="btn ghost" data-close>Stäng</button>';q('[data-close]').onclick=close}}
 return {destroy:close,isBusy:()=>busy};
}
