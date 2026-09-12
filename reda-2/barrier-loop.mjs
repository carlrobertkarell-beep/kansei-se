import {adaptationOptions} from './everyday-support.mjs?v=1';
import {cleanProgression} from './plan-authoring-model.mjs?v=2';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const barrierPhases={needs_context:'En snabbfråga återstår',ready:'Förslag att granska',trying:'Patienten provar ändringen',check_result:'Inväntar riktat svar',helped:'Hindret blev lättare',needs_review:'Nytt underlag att bedöma',superseded:'Planen har ändrats',handled:'Hanterat av behandlaren'};
export const outcomeLabels={helped:'Ja, det fungerade',partly:'Delvis',no:'Nej, fortfarande svårt',not_tried:'Har inte kunnat prova'};
export function contextText(l){const c=l.context;if(!c)return 'Inväntar patientens svar';return l.barrier==='time'?c.minutes+' minuter tillgängligt':[c.equipment==='home'?'Hemma':'Gym',c.band?'Har gummiband':'Utan gummiband',c.floorOK?'Golvövningar fungerar':'Utan golvövningar'].join(' · ')}
export function barrierCandidates(detail,base,P,D,loopId=null){
 if(!base||detail.cases?.some(c=>c.status!=='resolved'&&c.code==='changed_symptoms'))return [];
 const loops=(detail.barriers||[]).filter(l=>(!loopId||l.id===loopId)&&l.phase==='ready'&&!l.blocked&&l.source_plan_id===detail.patient?.plan_id&&l.context);
 return loops.slice(0,1).flatMap(l=>adaptationOptions(P,D,base,l.barrier).filter(x=>l.barrier==='time'||x.id==='band'&&!l.context.band||x.id==='floor'&&!l.context.floorOK||x.id==='home'&&l.context.equipment==='home').map(x=>{
  const plan=cleanProgression(x.plan);delete plan.planOptions;
  return {...x,id:l.id+':'+x.id,loopId:l.id,barrier:l.barrier,context:l.context,plan,
   title:(l.barrier==='time'?'Mer utrymme i vardagen':'Träning där patienten är')+' · '+x.title,
   detail:contextText(l)+'. '+x.detail+(l.barrier==='time'?' Antalet omgångar minskar; den faktiska passtiden behöver prövas.':'')+' Efter ett pass med ändringen frågar Reda om just hindret blev lättare.'};
 }));
}
export function clinicBarriersHTML(loops=[]){return loops.length?'<section class="barrier-clinic"><p class="eyebrow">EI följer hela vägen</p>'+loops.slice(0,5).map(l=>'<article><div><b>'+esc(l.barrier==='time'?'Få träningen att rymmas':'Få plats och utrustning att fungera')+'</b><span class="barrier-pill">'+esc(barrierPhases[l.phase])+'</span></div><p>'+esc(contextText(l))+'</p>'+(l.outcome?'<p><b>Patientens svar:</b> '+esc(outcomeLabels[l.outcome])+'</p>':'')+(l.result_version?'<small>Prövar plan v'+Number(l.result_version)+(l.due_date?' · Följ upp uteblivet svar '+esc(l.due_date):'')+'</small>':'')+(l.overdue?'<p class="barrier-overdue">Svar saknas efter uppföljningsdatumet. Stäm av med patienten.</p>':'')+(l.phase==='ready'?'<button type="button" class="btn primary" data-review-barrier="'+esc(l.id)+'">Granska ändringen och uppföljningen</button>':'')+(l.phase==='needs_context'?'<small>Snabbfrågan visas nästa gång patienten öppnar Reda.</small>':'')+'</article>').join('')+'</section>':''}

export function patientBarrierCopy(l){
 const time=l.barrier==='time';
 return ({needs_context:{title:time?'Hur mycket tid skulle fungera?':'Vad har du tillgång till?',detail:time?'Du berättade att tiden inte räckte. Ett snabbt val hjälper din behandlare att anpassa upplägget.':'Du berättade att plats eller utrustning saknades. Välj det som fungerar för dig.'},ready:{title:'Ditt svar är med i nästa steg',detail:'Din behandlare kan nu granska en ändring utifrån dina förutsättningar. Här ser du när en ny plan är klar.'},trying:{title:'Nu provar vi det nya upplägget',detail:time?'Din behandlare har godkänt en ändring för att göra passet lättare att hinna med. Efter ett pass frågar vi om tiden fungerade.':'Din behandlare har godkänt en ändring för din plats och utrustning. Efter ett pass frågar vi om den fungerade.'},check_result:{title:time?'Blev passet lättare att hinna med?':'Fungerade det med din plats och utrustning?',detail:'Du har registrerat ett pass med den uppdaterade planen. Ett snabbt svar hjälper oss att följa upp just ändringen.'},helped:{title:'Vi tar med det som fungerade',detail:'Du uppgav att ändringen hjälpte. Det praktiska hindret är avslutat. Du kan fortfarande be om hjälp och berätta hur kroppen svarar.'},needs_review:{title:l.outcome?'Ditt svar hjälper oss vidare':'Din behandlare behöver bedöma läget',detail:l.outcome?'Din behandlare får svaret tillsammans med ändringen du provat. Uppföljningen är öppen tills nästa steg är bedömt.':'Det finns återkoppling som behöver bedömas innan en ny anpassning föreslås.'},superseded:{title:'Du har fått en annan plan',detail:'Den här ändringen hör till en tidigare version. Din behandlare kan följa historiken.'},handled:{title:'Uppföljningen är hanterad',detail:'Din behandlare har avslutat ärendet. Du kan lämna ny återkoppling när något ändras.'}})[l.phase];
}
export function mountPatientBarriers(host,{api,patientId,onChanged,onPlan,onState}){
 if(!host||!api.patientBarriers)return null;
 let rows=[],alive=true,busy=false,ticket=0,error='',pending=null,values={},selectedId=null,receipt='';
 const q=s=>host.querySelector(s);
 function current(){return rows.find(l=>l.id===selectedId)||rows.find(l=>['needs_context','check_result'].includes(l.phase))||rows.find(l=>!['helped','handled','superseded'].includes(l.phase))||rows[0]}
 function render(){
  const l=current();host.hidden=!l&&!error;onState?.(l||null);
  if(!l){host.innerHTML=error?'<section class="card barrier-card"><p role="alert">'+esc(error)+'</p><button class="btn ghost" data-barrier-refresh>Försök igen</button></section>':'';q('[data-barrier-refresh]')?.addEventListener('click',refresh);return}
  const copy=patientBarrierCopy(l),step=l.phase==='needs_context'?0:l.phase==='ready'?1:l.result_plan_id?2:1;
  host.innerHTML='<section class="card barrier-card" data-barrier-phase="'+esc(l.phase)+'"><div class="barrier-kicker"><span class="ei-orbit" aria-hidden="true">ei</span><span>Din plan, i din vardag</span></div>'+ (rows.filter(r=>!['superseded','handled'].includes(r.phase)).length>1?'<label class="barrier-switch">Välj uppföljning<select data-barrier-switch>'+rows.map(r=>'<option value="'+esc(r.id)+'" '+(r.id===l.id?'selected':'')+'>'+esc((r.barrier==='time'?'Tid':'Plats och utrustning')+' · '+barrierPhases[r.phase])+'</option>').join('')+'</select></label>':'')+'<h2 tabindex="-1">'+esc(copy?.title||'Din uppföljning')+'</h2><p>'+esc(copy?.detail||'')+'</p><ol class="barrier-steps" aria-label="Så går uppföljningen till">'+['Dina förutsättningar','Granskad ändring','Fungerade det?'].map((t,i)=>'<li '+(i===step?'aria-current="step"':'')+'><span aria-hidden="true">'+(i<step||l.phase==='helped'?'✓':i+1)+'</span>'+t+'</li>').join('')+'</ol>'+
  (l.phase==='needs_context'?contextForm(l):'')+
  (l.phase==='check_result'?'<div class="loop-options barrier-outcomes">'+['helped','partly','no'].map(v=>'<button type="button" data-barrier-outcome="'+v+'">'+esc(outcomeLabels[v])+'</button>').join('')+'</div>':'')+
  (l.phase==='trying'?'<button type="button" class="btn primary" data-barrier-plan>Se mitt uppdaterade pass</button><details class="barrier-not-tried"><summary>Jag har inte kunnat prova</summary><p>Berätta för din behandlare att upplägget ännu inte har kunnat prövas.</p><button type="button" class="btn ghost" data-barrier-outcome="not_tried">Spara att jag inte kunnat prova</button></details>':'')+
  (l.context?'<p class="barrier-context">'+esc(contextText(l))+(l.result_version?' · Plan v'+Number(l.result_version):'')+'</p>':'')+
  '<p data-barrier-status role="'+(error?'alert':'status')+'">'+esc(error||receipt)+'</p><button type="button" class="barrier-refresh" data-barrier-refresh>Uppdatera uppföljningen</button></section>';
  q('[data-barrier-switch]')?.addEventListener('change',e=>{selectedId=e.target.value;values={};error='';receipt='';render()});
  q('[data-barrier-refresh]').onclick=refresh;q('[data-barrier-plan]')?.addEventListener('click',onPlan);
  host.querySelectorAll('[data-context-choice]').forEach(b=>b.onclick=()=>{values={...values,[b.dataset.key]:JSON.parse(b.dataset.value)};error='';render();host.querySelector('[data-context-choice][data-key="'+b.dataset.key+'"][data-value=\''+b.dataset.value+'\']')?.focus({preventScroll:true})});
  q('[data-barrier-save]')?.addEventListener('click',()=>save('context',values));
  host.querySelectorAll('[data-barrier-outcome]').forEach(b=>b.onclick=()=>save('outcome',b.dataset.barrierOutcome));
  if(busy)host.querySelectorAll('button,select').forEach(b=>b.disabled=true);
 }
 function contextForm(l){
  const group=(label,key,items)=>'<fieldset><legend>'+label+'</legend><div class="loop-options">'+items.map(([value,label])=>'<button type="button" data-context-choice data-key="'+key+'" data-value=\''+JSON.stringify(value)+'\' aria-pressed="'+String(values[key]===value)+'">'+label+'</button>').join('')+'</div></fieldset>';
  let ready=l.barrier==='time'?Number.isFinite(values.minutes):typeof values.band==='boolean'&&typeof values.floorOK==='boolean'&&values.equipment;
  return (l.barrier==='time'?group('Ungefär hur lång tid får ett pass ta?','minutes',[5,10,15,20,30,45,60].map(v=>[v,v+' min'])):group('Var vill du träna?','equipment',[['home','Hemma'],['gym','På gym']])+group('Har du gummiband?','band',[[true,'Ja'],[false,'Nej']])+group('Fungerar det att träna på golvet?','floorOK',[[true,'Ja'],[false,'Nej']]))+'<button type="button" class="btn primary" data-barrier-save '+(!ready?'disabled':'')+'>Spara mina förutsättningar</button>';
 }
 async function save(kind,input){
  if(busy)return;++ticket;const l=current(),sig=JSON.stringify([l.id,kind,input]);if(pending?.sig!==sig)pending={id:crypto.randomUUID(),sig};busy=true;error='';receipt='';render();
  try{const row=kind==='context'?await api.answerBarrier(l.id,pending.id,input):await api.barrierOutcome(l.id,pending.id,input,input==='not_tried'?null:l.session_id);
   if(!alive)return;if(row?.id!==l.id)throw Error('Sparningen kunde inte bekräftas. Försök igen.');
   rows=rows.map(x=>x.id===row.id?row:x);selectedId=row.id;values={};pending=null;receipt='Ditt svar är sparat.';
   try{await onChanged?.(row)}catch{receipt+=' Övrig status uppdateras när du hämtar sidan igen.'}
  }catch(e){if(alive)error=e.message||'Svaret kunde inte sparas. Dina val finns kvar.'}finally{busy=false;if(alive){render();if(!error)q('h2')?.focus({preventScroll:true})}}
 }
 async function refresh(){if(busy||!alive)return;const n=++ticket;try{const result=await api.patientBarriers(patientId);if(!alive||n!==ticket)return;rows=result;error='';render()}catch{if(alive&&n===ticket){error='Uppföljningen kunde inte hämtas. Försök igen.';render()}}}
 refresh();return {refresh,isBusy:()=>busy,destroy(){alive=false;++ticket;host.replaceChildren()},focus(){q('h2')?.focus();host.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}};
}
