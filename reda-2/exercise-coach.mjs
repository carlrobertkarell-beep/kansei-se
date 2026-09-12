import {HELP_VERSION,helpTopics,helpAnswer,sideLabels} from './exercise-help-model.mjs?v=20260912-coach1';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function createExerciseCoach(host,{api,onDemonstrate,onSaved,onBusy,preview=false}){
 if(!host)return null;
 let alive=true,busy=false,context=null,key=null,states=new Map(),state=null;
 const valid=()=>alive&&host.isConnected,q=s=>host.querySelector(s);
 function status(message){if(valid())q('[data-coach-status]').textContent=message}
 function draw(){
  if(!context||!valid())return;
  const x=context.exercise,a=helpAnswer(x,state.topic);
  host.innerHTML=`<details class="exercise-coach" ${state.open?'open':''}><summary><span><b>Osäker på något?</b><small>Få hjälp med just den här övningen</small></span><span aria-hidden="true">+</span></summary><div class="coach-body"><p class="coach-context">${esc(x.name)} · ${esc(sideLabels[x.side]||'Sida behöver förtydligas')} · plan v${esc(context.plan.version)}</p><div class="coach-topics" role="group" aria-label="Vad vill du få förklarat?">${Object.entries(helpTopics).map(([t,l])=>`<button type="button" data-coach-topic="${t}" aria-pressed="${state.topic===t}">${l}</button>`).join('')}</div><section class="coach-answer" aria-labelledby="coachAnswerTitle" ${a?'':'hidden'}><p class="eyebrow">Från din sparade plan</p><h3 id="coachAnswerTitle" tabindex="-1">${esc(a?.title||'')}</h3>${a?'<ol>'+a.paragraphs.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>':''}${a?.frame!==null&&a?'<button type="button" class="coach-show" data-coach-show>Visa i illustrationen ↑</button>':''}</section><div class="coach-outcome" ${state.topic&&!state.receipt?'':'hidden'}><p><b>Blev det tydligt?</b></p><div class="coach-actions"><button type="button" class="btn primary" data-coach-clear>Ja, nu förstår jag</button><button type="button" class="btn ghost" data-coach-contact>Jag behöver behandlaren</button></div><form data-coach-form ${state.contact?'':'hidden'}><label>Vill du lägga till något? <span class="sub">Valfritt</span><textarea maxlength="500" rows="2" placeholder="Berätta vad du fortfarande undrar över.">${esc(state.note)}</textarea></label><p>Övningen, planversionen och vilka förklaringar du öppnat följer med.</p><button type="submit" class="btn primary">Be behandlaren om hjälp</button><p class="sub">Svar visas i Reda. Förfrågan bevakas inte i realtid.</p></form></div><p class="coach-status" data-coach-status role="status" aria-live="polite">${esc(state.receipt?(preview?'Förhandsvisning klar. Inget har skickats eller sparats.':state.receipt.outcome==='clear'?'Sparat: du upplever instruktionen som tydlig.':'Din fråga är sparad hos kliniken med övningen och underlaget.'):state.message||'')}</p>${state.receipt?'<button type="button" class="coach-show" data-coach-new>Jag har en annan fråga</button>':''}<p class="coach-contact"><a href="/kontakt/">Klinikens kontaktuppgifter</a></p></div></details>`;
  q('details').ontoggle=()=>{state.open=q('details').open};
  host.querySelectorAll('[data-coach-topic]').forEach(b=>b.onclick=()=>{
   if(busy)return;state.topic=b.dataset.coachTopic;state.open=true;state.topics=[...new Set([...state.topics,state.topic])];state.message='';draw();q('[data-coach-topic="'+state.topic+'"]').focus({preventScroll:true});
   const a=helpAnswer(context.exercise,state.topic);onDemonstrate?.(a.frame,a.focus);
  });
  q('[data-coach-show]')?.addEventListener('click',()=>{onDemonstrate?.(a.frame,a.focus,true)});
  q('[data-coach-clear]')?.addEventListener('click',()=>save('clear'));
  q('[data-coach-contact]')?.addEventListener('click',()=>{if(busy)return;state.contact=true;q('[data-coach-form]').hidden=false;q('textarea').focus()});
  q('textarea')?.addEventListener('input',()=>{state.note=q('textarea').value});
  q('form').onsubmit=e=>{e.preventDefault();save('needs_help')};
  q('[data-coach-new]')?.addEventListener('click',()=>{states.delete(key);setExercise(context);state.open=true;draw();q('[data-coach-topic]').focus()});
 }
 async function save(outcome){
  if(busy||!state?.topics.length||state.receipt)return;
  if(!api.submitExerciseHelp){status('Återkopplingen kunde inte öppnas. Du kan använda klinikens kontaktuppgifter.');return}
  const captured=state,ctx=context,body={topics:[...state.topics],outcome,note:outcome==='needs_help'?state.note.trim():'',version:HELP_VERSION};
  const signature=JSON.stringify([ctx.plan.id,ctx.sessionId,ctx.exercise.id,body]);
  if(state.pending?.signature!==signature)state.pending={signature,id:crypto.randomUUID()};
  busy=true;onBusy?.(true);host.querySelectorAll('button,textarea').forEach(b=>b.disabled=true);status('Sparar…');
  try{
   const receipt=await api.submitExerciseHelp(ctx.sessionId,ctx.exercise.id,captured.pending.id,body);
   captured.receipt=receipt;captured.pending=null;captured.message='';
   if(valid()&&captured===state){draw();q('[data-coach-status]').setAttribute('tabindex','-1');q('[data-coach-status]').focus({preventScroll:true})}
   onSaved?.(receipt);
  }catch(e){captured.message=e.message||'Kunde inte bekräfta sparningen. Dina val är kvar. Försök igen.';if(valid()&&captured===state){draw();status(captured.message)}}
  finally{busy=false;onBusy?.(false);if(valid())host.querySelectorAll('button,textarea').forEach(b=>b.disabled=false)}
 }
 function setExercise(next){
  if(busy)return false;
  context=next;key=[next.plan.id,next.sessionId,next.exercise.id].join(':');
  if(!states.has(key))states.set(key,{open:false,topic:null,topics:[],contact:false,note:'',receipt:null,pending:null,message:''});
  state=states.get(key);draw();return true;
 }
 return {setExercise,isBusy:()=>busy,destroy(){alive=false;states.clear();host.replaceChildren()}};
}
