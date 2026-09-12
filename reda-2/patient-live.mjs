import {createMovementLesson} from './movement-lesson.mjs?v=2';
import {createExerciseCoach} from './exercise-coach.mjs?v=20260912-coach1';
import {exerciseSide,sideLabels} from './exercise-help-model.mjs?v=20260912-coach1';
import {mountPatientBarriers} from './barrier-loop.mjs?v=1'
let barriers=null;
import {startHTML} from './first-patient-steps.mjs?v=2'
let planMessage='',signedIn=false;
import {mountPatientCheckin} from './patient-basis.mjs?v=1'
let checkin=null;
import {mountPatientSupport} from './support-workflow.mjs?v=2'
let support=null;
import {mountActivityLog} from './activity-log.mjs?v=1'
let activity=null;
import {approvedOptions,optionPlan} from './plan-options.mjs?v=1'
window.RedaPlanOptions={optionPlan};
let selectedOption=null;
import {mountSavedSupport,openPlanGuide} from './plan-guide.mjs?v=2'
import * as api from './secure-browser.mjs?v=20260912-coach1'
import {todayState,pendingReflections} from './patient-loop.mjs?v=2'
import {mountSessionReflection} from './session-reflection.mjs?v=4'
import {mountPatientMessages} from './patient-messages.mjs?v=2'
let messages=null;
import {mountPlanHelp,decisionText} from './runtime-ui.mjs?v=20260912-coach1'
const $=id=>document.getElementById(id), F=window.RedaFigures, S=window.RedaSession, R=window.RedaRecovery
let helpExpanded=true,coach=null;
const lesson=createMovementLesson($('movementLesson'),{onReady:()=>{$('rounds').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});($('rounds').querySelector('button:not(:disabled)')||$('next'))?.focus({preventScroll:true})}});
let state=null,plan=null,session=null,index=0, syncQueue=Promise.resolve(), unsynced=false, syncVersion=0, lastSynced=0, starting=false, recoveryBlocked=false, durable=false, previousSession=null
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
function setAuth(show){$('auth').classList.toggle('hidden',!show);$('app').classList.toggle('hidden',show);$('logout').classList.toggle('hidden',show)}
function error(e){if(signedIn){$('logout').classList.remove('hidden');$('retryAccess').classList.remove('hidden')}else $('retryAccess').classList.add('hidden');$('authSuccess').classList.add('hidden');$('authError').textContent=e?.message||String(e);$('authError').classList.remove('hidden')}
function sessionPlan(){return plan?optionPlan(plan,session&&!session.completedAt?session.optionId:selectedOption):null}
function exercises(){return sessionPlan()?.payload?.exercises||[]}
const I=window.RedaIntelligence,TR=window.RedaTrainingResponse;
const responseForm=window.RedaResponseForm.create($('responseForm'),{submit:(sid,rid,answers)=>api.submitTrainingResponse(sid,rid,answers),onSaved:row=>{state.responses=[...(state.responses||[]).filter(x=>x.session_id!==row.session_id),row];renderResponsePrompt();support?.refresh();barriers?.refresh();evaluateNext()}});
const reflectionForm=mountSessionReflection($('sessionReflection'),{submit:(sid,rid,answers)=>api.submitSessionReflection(sid,rid,answers),onSaved:row=>{state.reflections=[...(state.reflections||[]).filter(x=>x.session_id!==row.session_id),row];renderReflectionPrompt();renderSavedSupport();$('patientStart').innerHTML=startHTML(state,planMessage);support?.refresh();barriers?.refresh()},onBarrier:()=>{barriers?.refresh().then(()=>barriers?.focus())},onLater:()=>{$('todayTitle').scrollIntoView({block:'start',behavior:'smooth'})}});
function renderReflectionPrompt(){
 const host=$('reflectionPrompt');if(!api.submitSessionReflection){host.hidden=true;return}
 if(state.reflectionError){host.hidden=false;host.textContent='Dina svar direkt efter passen kunde inte hämtas. Ladda om för att försöka igen.';return}
 const candidate=pendingReflections(plan,state.sessions,state.reflections)[0];host.hidden=!candidate;
 host.innerHTML=candidate?'<p>Passet är sparat. Berätta kort hur det fungerade.</p><button type="button" class="btn ghost" id="openReflection">Två snabba frågor</button>':'';
 $('openReflection')?.addEventListener('click',()=>openReflection(candidate));
}
function openReflection(row){if(!row||row.plan_id!==plan.id||state.reflectionError||!api.submitSessionReflection)return;document.querySelector('[data-tab="today"]').click();reflectionForm.show({userId:state.userId,session:row,plan:optionPlan(plan,row.payload?.optionId)});reflectionForm.focus()}
function renderSavedSupport(){
 const row=[...(state.reflections||[])].filter(r=>r.plan_id===plan.id).sort((a,b)=>new Date(b.created_at)-new Date(a.created_at))[0];
 $('savedSupport').hidden=!row||!!state.reflectionError;
 if(row&&!state.reflectionError)mountSavedSupport($('savedSupportContent'),{row,plan:optionPlan(plan,state.sessions.find(s=>s.id===row.session_id)?.payload?.optionId)});else $('savedSupportContent').replaceChildren();
}
$('patientNext').onclick=()=>barriers?.focus();
$('openPlanGuide').onclick=()=>openPlanGuide(sessionPlan());
function renderOptions(){
 const host=$('planOptionChoice');let options=[];try{options=approvedOptions(plan.payload)}catch(e){host.hidden=false;host.textContent=e.message;$('start').disabled=true;return}
 const open=!!session&&!session.completedAt;host.hidden=!options.length;
 if(!options.length){if(!open)selectedOption=null;return}
 if(open)selectedOption=session.optionId||null;
 if(selectedOption&&!options.some(o=>o.id===selectedOption))selectedOption=null;
 host.innerHTML='<h3>Vad fungerar idag?</h3><p>Välj bland alternativen din behandlare har granskat. Vid nya eller ökade besvär, kontakta kliniken för bedömning.</p><div class="loop-options">'+[{id:'',label:'Ordinarie pass'},...options].map(o=>'<button type="button" data-session-option="'+esc(o.id)+'" aria-pressed="'+String((selectedOption||'')===o.id)+'" '+(open?'disabled':'')+'>'+esc(o.label)+'</button>').join('')+'</div><p class="sub">'+(open?'Ditt påbörjade pass behåller det valda alternativet.':'Valet gäller det här passet. Grundplanen är kvar.')+'</p>';
 host.querySelectorAll('[data-session-option]').forEach(b=>b.onclick=()=>{if(starting||session&&!session.completedAt)return;selectedOption=b.dataset.sessionOption||null;renderToday()});
}
function renderToday(){
 renderOptions();$('exerciseCount').textContent=exercises().length;const view=todayState(plan,state.sessions);$('todayCard').dataset.dayState=view.kind;$('todayTitle').textContent=view.title;$('todayDetail').textContent=view.detail;
 $('todayExercises').innerHTML=exercises().map(x=>'<li><span class="patient-exercise-index">'+String(exercises().indexOf(x)+1).padStart(2,'0')+'</span><span><b>'+esc(x.name)+'</b><small>'+esc(doseLabel(x))+(x.side==='both'?' · båda sidor':x.side==='left'?' · vänster':x.side==='right'?' · höger':'')+'</small></span></li>').join('');
 if(!session||session.completedAt)$('start').textContent=view.button;
 renderReflectionPrompt();renderSavedSupport();
}
function renderResponsePrompt(){const n=state.responseError?0:TR.due(state.sessions,state.responses).length;$('responsePrompt').classList.toggle('hidden',!n);$('responsePrompt').innerHTML=n?'<b>Hur svarade kroppen efter träningen?</b><br>Du kan lämna återkoppling på ett tidigare pass.<br><button type="button" class="btn ghost" id="openResponse">Svara på frågorna</button>':'';$('openResponse')?.addEventListener('click',()=>document.querySelector('[data-tab="follow"]').click())}
function renderIntelligence(){const o=I.overview(plan.payload);$('intelligenceContext').innerHTML='<p class="eyebrow">Din utgångspunkt</p><h3>'+esc(o.goalLabel)+'</h3><p>'+esc(o.contextKnown?o.focus:'Din behandlares sparade ordination visas nedan.')+'</p><details class="ei-plan-context"><summary>Vad planen tar hänsyn till</summary><dl class="ei-axes">'+o.axes.map(x=>'<div><dt>'+esc(x.label)+'</dt><dd>'+esc(x.value)+'</dd></div>').join('')+'</dl><p class="ei-footnote">Exercise Intelligence samlar förutsättningar, övningsval och återkoppling. Du följer alltid den aktuella ordinationen.</p></details>';responseForm.render(state);renderResponsePrompt()}
function pauseMotion(){lesson.pause()}
function currentSide(x){const rounds=S.rounds(x),p=session?.progress[index];return exerciseSide(x,rounds[Math.min(p?.roundsDone||0,rounds.length-1)])}
function renderExerciseHelp(x){const h=I.exercise(sessionPlan().payload,x),expanded=helpExpanded??plan.payload.presentation!=='trained';$('exerciseHelp').innerHTML='<button type="button" class="ei-help-toggle" id="helpToggle" aria-expanded="'+expanded+'">'+(expanded?'Visa kortare instruktion':'Visa steg för steg')+'</button>'+(expanded?'<p class="ei-setup">'+h.setup.map(esc).join(' · ')+'</p><ol class="ei-instructions">'+h.steps.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>':'')+(h.range?'<p class="ei-setup">Ordinerat rörelseomfång: '+esc(h.range)+'</p>':'')+(h.rest!==null?'<p class="ei-setup">Ordinerad vila: '+h.rest+' sekunder mellan omgångarna.</p>':'');$('helpToggle').onclick=()=>{helpExpanded=!expanded;renderExerciseHelp(x)}}
function renderCare(){
 try{
  const c=window.RedaCare.overview(plan.payload),next=c.next;
  const summary=document.querySelector('.hero .notice summary');if(summary)summary.textContent=next?'Nästa uppföljning · '+next.dateLabel:'Din planerade uppföljning';
  $('reviewText').textContent=next?`${next.label}: ${next.dateLabel} · ${next.contact}. Tid bekräftas separat. Din behandlare bedömer om planen ska ändras.`:c.unconfirmedPast?'De planerade datumen har passerat. Kontakta din behandlare för att bekräfta nästa avstämning.':'Ni kommer överens om nästa avstämning. Din behandlare bedömer nästa steg, på kliniken eller på distans.';
  $('careOverview').innerHTML=`<section class="care-overview"><p class="eyebrow">Ditt kontaktupplägg</p><h3>${esc(c.label)}${c.weeks?' · '+c.weeks+' veckor':''}</h3>${c.weeks?`<p>Planerad period: ${esc(window.RedaCare.displayDate(c.startDate))}–${esc(window.RedaCare.displayDate(c.endDate))}</p>`:''}<p>Här ser du kontakterna i din plan. Bokad tid och eventuell samtalslänk får du separat från Kansei.</p><ol class="care-timeline">${c.points.map((p,i)=>`<li><span class="care-num">${String(i+1).padStart(2,'0')}</span><div><strong>${esc(p.label)}</strong><small>${esc(p.dateLabel)} · ${esc(p.contact)}</small>${p.passed?'<small class="past-contact">Datum passerat · genomförande bekräftas med behandlaren</small>':''}</div></li>`).join('')||'<li><div><strong>Vi planerar nästa kontakt tillsammans.</strong><small>Inget datum är angivet i din plan ännu.</small></div></li>'}</ol><div class="care-preparation"><h4>Inför avstämningen</h4><p>Fundera på vilka övningar som fungerat, vad som varit svårt och hur det går med ditt mål. Dina registreringar är ett underlag när ni följer upp tillsammans.</p></div><p>En avstämning eller avslutad period ändrar inte träningsnivån automatiskt. Nästa steg beslutas med din behandlare.</p><a href="/kontakt/">Kontakta Kansei ↗</a></section>`;
 }catch{$('reviewText').textContent='Kontakta din behandlare för att bekräfta nästa uppföljning.';$('careOverview').innerHTML='<p class="muted">Kontaktplaneringen kunde inte visas. Kontakta Kansei för datum och kontaktform.</p>'}
}

function doseLabel(x){return x?.dose?.label||[x?.dose?.sets&&`${x.dose.sets} omgångar`,x?.dose?.reps&&`${x.dose.reps} repetitioner`].filter(Boolean).join(' · ')||'Följ ordinationen'}
function sets(x){return S.rounds(x).length}
function instruction(x){return x?.instruction||x?.instructions?.[0]||x?.steps?.[0]||x?.cue||'Följ rörelsen lugnt och kontrollerat enligt din ordination.'}
function motionKey(x){return x?.motionKey||x?.motion?.key||x?.figure||x?.variantId||x?.id}
function prescription(x){const p=x?.prescription;if(!p)return (x?.prescribedLoad?'<p><b>Ordinerad belastning</b><br>'+esc(x.prescribedLoad)+'</p>':'')+(x?.prescribedRange?'<p><b>Ordinerat rörelseomfång</b><br>'+esc(x.prescribedRange)+'</p>':'');return `<div class="prescription-grid"><div><span>Tränar</span><b>${esc(p.target)}</b></div><div><span>Rörelse</span><b>${esc(x.prescribedRange||p.rom)}</b></div><div><span>Tempo</span><b>${esc(p.tempo)}</b></div><div><span>Belastning</span><b>${esc(x.prescribedLoad||p.load)}</b></div></div><div class="measure-line"><span>Det vi kan följa</span><b>${esc(p.measure)}</b></div>`}
function whyBlock(x){const why=x?.why||'',focus=x?.focus||'',level=x?.challenge||'';if(!why&&!focus&&!level&&!x?.prescription&&!x?.prescribedRange&&!x?.prescribedLoad)return'';return `<div class="exercise-context">${level?`<span class="level-pill">${esc(level)}</span>`:''}${why?`<div><b>Varför den här är med</b><p>${esc(why)}</p></div>`:''}${prescription(x)}${focus?`<div><b>Ditt fokus</b><p>${esc(focus)}</p></div>`:''}</div>`}
function renderHome(){if($('patientDate'))$('patientDate').textContent=new Intl.DateTimeFormat('sv-SE',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Stockholm'}).format(new Date());if($('patientStart'))$('patientStart').innerHTML=startHTML(state,planMessage);const xs=plan.payload.exercises||[];$('patientName').textContent=state.patient.display_name;$('version').textContent=plan.version;$('exerciseCount').textContent=xs.length;$('todayMeta').textContent=plan.payload?.schedule?.days?.length?`${plan.payload.schedule.days.length} planerade pass/vecka`:'Enligt din plan';$('intro').textContent=plan.payload?.goal?`Målet med den här perioden: ${plan.payload.goal}`:'Det här är den plan du och din behandlare har gått igenom.';renderCare();renderIntelligence();const helpPlan=plan;mountPlanHelp($('planHelp'),{api,plan,isCurrent:()=>plan===helpPlan,onResponse:()=>document.querySelector('[data-tab=follow]').click()});$('programList').innerHTML=xs.map((x,i)=>`<div class="exercise program-exercise"><div class="exercise-topline"><span>${String(i+1).padStart(2,'0')}</span><span>${esc(x.challenge||'Individuell nivå')}</span></div><h3>${esc(x.name)}</h3><div class="sub">${esc(x.variantLabel||'')} · ${esc(doseLabel(x))}</div>${whyBlock(x)}</div>`).join('');renderHistory();renderToday()}
function renderHistory(){const rows=state.sessions||[];$('history').innerHTML=rows.length?rows.map(s=>`<div class="exercise"><b>${s.status==='completed'?'Genomfört':s.status==='partial'?'Delvis genomfört':s.status==='started'?'Påbörjat':'Planerad vila'}</b><div class="sub">${new Date(s.started_at).toLocaleDateString('sv-SE')} · plan v${s.plan_version}${s.payload?.optionId?' · Godkänt alternativ: '+esc((s.plan_id===plan.id?plan.payload.planOptions?.items?.find(o=>o.id===s.payload.optionId)?.label:null)||s.payload.optionId):''}</div></div>`).join(''):'<p class="muted">Ingen träningshistorik ännu.</p>'}
async function bootstrap(){
 state=await api.patientBootstrap();plan=state.plan;selectedOption=null;planMessage='';if(api.openPatientPlan)try{const h=await api.openPatientPlan(plan.id);planMessage=h.message||''}catch{planMessage='Planen visas, men kliniken har ännu inte fått kvitto på att du öppnat den.'}
 const restored=R.choose(plan,state.sessions,R.read(localStore(),state.userId));
 if(restored.discard)R.clear(localStore(),state.userId);
 recoveryBlocked=!!restored.blocked;previousSession=restored.previous||null;$('closePrevious').classList.toggle('hidden',!previousSession);session=restored.session||null;index=restored.index||0;
 renderHome();setAuth(false);barriers?.destroy();barriers=mountPatientBarriers($('patientBarrier'),{api,patientId:state.patient.id,onChanged:()=>support?.refresh(),onState:l=>{const actionable=['needs_context','check_result'].includes(l?.phase);$('patientBarrier').dataset.actionable=String(actionable);$('patientNext').hidden=!actionable;$('patientNextLabel').textContent=l?.phase==='check_result'?'Hjälpte ändringen du provade?':'En snabbfråga om '+(l?.barrier==='time'?'din tid':'plats och utrustning')},onPlan:()=>{document.querySelector('[data-tab=today]').click();$('todayTitle').focus();$('todayCard').scrollIntoView({block:'start',behavior:'smooth'})}});checkin?.destroy();checkin=mountPatientCheckin($('patientCheckin'),{api,patientId:state.patient.id,onSaved:()=>{support?.refresh();barriers?.refresh()}});if(!messages)messages=mountPatientMessages($('patientMessages'),{api,onSent:()=>support?.refresh()});support?.destroy();support=mountPatientSupport($('patientSupport'),{api,patientId:state.patient.id,onMessages:async()=>{await messages?.refresh();const el=$('patientMessages');el.querySelector('details').open=true;el.scrollIntoView({block:'start',behavior:'smooth'});el.querySelector('textarea')?.focus()}});$('start').disabled=recoveryBlocked;
 $('start').textContent=session&&!session.completedAt?'Fortsätt påbörjat pass':todayState(plan,state.sessions).button;
 $('sync').textContent=restored.message||(session?'Ditt påbörjade pass är återställt.':'Synkad med kliniken');
 if(restored.retry)await sync(session.status,session.completedAt);
} 
function localStore(){try{return window.localStorage}catch{return null}}
function persist(){if(session&&state?.userId)durable=R.write(localStore(),state.userId,plan,session,index)}
function progressPayload(){return {...(session.optionId?{optionId:session.optionId}:{}),exercises:session.progress.map(p=>({exerciseId:p.exerciseId,status:p.status,roundsDone:p.roundsDone,feedback:p.feedback})),clientUpdatedAt:new Date().toISOString()}}
async function sync(status,completedAt=null){session.status=status;session.completedAt=completedAt;const data={clientSessionId:session.id,status,startedAt:session.startedAt,completedAt,payload:progressPayload()},planId=plan.id, version=++syncVersion;unsynced=true;persist();$('sync').textContent=durable?'Sparat på enheten · synkar med kliniken…':'Sparar passet…';syncQueue=syncQueue.then(async()=>{try{await api.saveSession(planId,data);lastSynced=version;unsynced=lastSynced<syncVersion;if(!unsynced)R.clear(localStore(),state.userId);$('retrySync').classList.add('hidden');$('sync').textContent=unsynced?'Sparar passet…':'Synkad med kliniken';return true}catch(e){unsynced=true;$('retrySync').classList.remove('hidden');$('sync').textContent=durable?'Sparat på den här enheten. Synkas när anslutningen fungerar.':'Passet är inte sparat. Behåll sidan öppen och försök igen.';return false}});return syncQueue}
async function start(){const xs=exercises();if(!xs.length||starting||recoveryBlocked||reflectionForm.isBusy()||coach?.isBusy())return;starting=true;$('start').disabled=true;try{if(session?.completedAt&&unsynced){$('sync').textContent='Synka det avslutade passet innan du börjar ett nytt.';return}if(!session||session.completedAt){const fresh=await api.patientBootstrap();let checked=false;if(fresh.plan.id!==plan.id){if(pendingEvaluation){checked=await evaluateNext()!==false;if(!checked){$('sync').textContent='Nästa steg kunde inte kontrolleras. Försök igen innan du startar ett nytt pass.';return}}if(!checked||plan.id!==fresh.plan.id){await bootstrap();$('sync').textContent='Din behandlare har uppdaterat planen. Läs den nya versionen innan du startar passet.';return}}if(!checked&&await evaluateNext()===false){$('sync').textContent='Nästa steg kunde inte kontrolleras. Försök igen innan du startar ett nytt pass.';return}session=null;session=S.create(exercises(),crypto.randomUUID(),new Date().toISOString());if(selectedOption)session.optionId=selectedOption;index=0;await sync('started')} $('start').textContent='Fortsätt passet';$('sessionReflection').hidden=true;$('player').classList.remove('hidden');$('app').dataset.playerOpen='true';renderOptions();showExercise();$('exName').focus({preventScroll:true});$('player').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}catch(e){$('sync').textContent=e.message||'Planen kunde inte kontrolleras. Försök igen.'}finally{starting=false;$('start').disabled=recoveryBlocked}}
function showExercise(){pauseMotion();const total=session.progress.reduce((n,p,i)=>n+sets(exercises()[i]),0),done=session.progress.reduce((n,p)=>n+p.roundsDone,0);if($('sessionProgress')){$('sessionProgress').max=total||1;$('sessionProgress').value=done;$('sessionProgressText').textContent=done+' av '+total+' omgångar registrerade'}const x=exercises()[index],p=session.progress[index];$('pos').textContent=`${index+1} av ${exercises().length}`;$('exName').textContent=x.name;$('dose').textContent=doseLabel(x)+(x.side==='both'?' per sida':x.side==='left'?' · vänster':x.side==='right'?' · höger':'')+(x.prescribedLoad?' · '+x.prescribedLoad:'');$('instruction').textContent=instruction(x);$('exerciseWhy').innerHTML=whyBlock(x);renderExerciseHelp(x);$('rounds').innerHTML=S.rounds(x).map((r,i)=>`<button class="btn ${i<p.roundsDone?'primary':'soft'} round" data-round="${i}" ${i!==p.roundsDone?'disabled':''}>${i<p.roundsDone?'✓ ':''}Omgång ${r.set}${r.side==='left'?' · vänster':r.side==='right'?' · höger':''}</button>`).join('');document.querySelectorAll('[data-effort]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.effort===p.feedback));b.onclick=async()=>{if(session.completedAt)return;p.feedback=b.dataset.effort;showExercise();await sync('partial')}});lesson.setExercise(x,{motionKey:motionKey(x),exerciseSide:currentSide(x),contextId:plan.id+':'+plan.version+':'+(session.optionId||'default')});coach?.setExercise({plan:sessionPlan(),exercise:x,sessionId:session.id});document.querySelectorAll('[data-round]').forEach(b=>b.onclick=()=>markRound(Number(b.dataset.round)));$('next').disabled=p.roundsDone<sets(x)&&p.status!=='skipped';$('next').textContent=index===exercises().length-1?'Avsluta pass':'Nästa övning'}
async function markRound(i){if(session?.completedAt||coach?.isBusy())return;session=S.mark(session,index,i);showExercise();await sync('partial')}
async function skip(){if(session?.completedAt||coach?.isBusy())return;const p=session.progress[index];p.status='skipped';showExercise();await sync('partial')}
async function next(){if(session?.completedAt||coach?.isBusy())return;if(index<exercises().length-1){index++;showExercise();$('exName').focus({preventScroll:true});$('player').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});if(unsynced)persist();return}$('next').disabled=true;const all=session.progress.every(p=>p.status==='completed'),doneAt=new Date().toISOString();const saved=await sync(all?'completed':'partial',doneAt);pauseMotion();$('player').classList.add('hidden');$('app').dataset.playerOpen='false';$('start').textContent='Starta nytt pass';if(saved){try{const finishedId=session.id;state=await api.patientBootstrap();plan=state.plan;renderHome();barriers?.refresh();$('sync').textContent=all?'Passet är sparat och synkat':'Passet är sparat som delvis genomfört';openReflection(pendingReflections(plan,state.sessions,state.reflections).find(x=>x.client_session_id===finishedId))}catch(e){$('sync').textContent='Passet är sparat, men historiken kunde inte uppdateras.'}}}
async function pause(){if(!session||session.completedAt||coach?.isBusy())return;$('player').classList.add('hidden');$('app').dataset.playerOpen='false';pauseMotion();$('start').focus({preventScroll:true});await sync(session.progress.some(p=>p.roundsDone||p.status==='skipped')?'partial':'started')}
$('magicLink').onclick=async()=>{try{const email=$('email').value.trim();if(!email)throw new Error('Ange din e-postadress');$('magicLink').disabled=true;$('authError').classList.add('hidden');await api.sendPatientMagicLink(email);$('authSuccess').textContent='Om adressen har ett Reda-konto får du ett mejl med en engångslänk. Öppna det senaste mejlet. Kontrollera även skräpposten.';$('authSuccess').classList.remove('hidden')}catch(e){error(e)}finally{$('magicLink').disabled=false}}
$('logout').onclick=async()=>{if(responseForm.isBusy()||reflectionForm.isBusy()||messages?.isBusy()||checkin?.isBusy()||barriers?.isBusy()||coach?.isBusy()){$('sync').textContent='Vänta tills återkopplingen har sparats eller ett felmeddelande visas.';return}if(unsynced){$('sync').textContent='Synka passet innan du loggar ut.';return}R.clear(localStore(),state?.userId);await api.signOut();location.reload()};$('start').onclick=start;$('skip').onclick=skip;$('next').onclick=next;$('closePlayer').onclick=pause
const tabScroll=new Map();let activeTab='today';
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{if(coach?.isBusy())return;const changed=activeTab!==b.dataset.tab;if(changed)tabScroll.set(activeTab,window.scrollY);if(b.dataset.tab!=='today')pauseMotion();if(b.dataset.tab==='activity'&&state){activity?.destroy();activity=mountActivityLog($('activityContent'),{api,patientId:state.patient.id})}document.querySelectorAll('[data-tab]').forEach(x=>{x.classList.toggle('active',x===b);if(x===b)x.setAttribute('aria-current','page');else x.removeAttribute('aria-current')});document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('hidden',x.id!==b.dataset.tab));activeTab=b.dataset.tab;if(changed)window.scrollTo({top:tabScroll.get(activeTab)||0,behavior:'instant'})})
setAuth(true);api.currentUser().catch(e=>{if(e?.name==='AuthSessionMissingError')return null;throw e}).then(async u=>{signedIn=!!u;if(u)await bootstrap()}).catch(error)
$('retryAccess').onclick=async()=>{try{$('retryAccess').disabled=true;await bootstrap();$('retryAccess').classList.add('hidden')}catch(e){error(e)}finally{$('retryAccess').disabled=false}};
const callbackError=new URLSearchParams(location.hash.slice(1)).get('error_code')||new URLSearchParams(location.search).get('error_code');if(callbackError){history.replaceState(null,'',location.pathname);error(new Error('Länken kunde inte användas. Ange din e-postadress för att få en ny länk och öppna det senaste mejlet.'))}
api.db?.auth.onAuthStateChange((event,session)=>{if(event==='SIGNED_IN'&&session&&!state){signedIn=true;setTimeout(()=>bootstrap().catch(error),0)}});
async function retry(){if(!session)return;const finished=!!session.completedAt;if(await sync(session.status,session.completedAt)){if(finished){try{await bootstrap()}catch{$('sync').textContent='Passet är sparat. Ladda om sidan för att uppdatera planen.'}}}}
$('retrySync').onclick=retry;window.addEventListener('beforeunload',e=>{if((unsynced&&!durable)||reflectionForm.isBusy()||checkin?.isBusy()||barriers?.isBusy()||coach?.isBusy()){e.preventDefault();e.returnValue=''}});

window.addEventListener('online',()=>{if(unsynced&&session)retry()});

$('closePrevious').onclick=async()=>{
 if(!previousSession)return;
 $('closePrevious').disabled=true;
 try{const {planId,...old}=previousSession,items=old.payload?.exercises||[];
  await api.saveSession(planId,{...old,status:items.length&&items.every(p=>p.status==='completed')?'completed':'partial',completedAt:new Date().toISOString()});
  R.clear(localStore(),state.userId);await bootstrap();
 }catch(e){$('sync').textContent='Det föregående passet kunde inte sparas. Dina markeringar är kvar; försök igen när du har anslutning.'}
 finally{$('closePrevious').disabled=false}
};





let evaluating=false,pendingEvaluation=null,evaluationTask=null;
function evaluateNext(){if(evaluationTask)return evaluationTask;evaluationTask=runEvaluation().finally(()=>{evaluationTask=null});return evaluationTask}
async function runEvaluation(){
 if(!api.evaluateProgression||!state||evaluating||unsynced||recoveryBlocked||reflectionForm.isBusy()||(session&&!session.completedAt))return;
 evaluating=true;const patientId=state.patient.id;pendingEvaluation=pendingEvaluation||crypto.randomUUID();
 try{const d=await api.evaluateProgression(patientId,pendingEvaluation);if(state.patient.id!==patientId)return false;
  if(d.applied&&d.result_plan_id){session=null;await bootstrap()}
  $('engineDecision').hidden=d.code==='no_frame';$('engineDecisionText').textContent=decisionText(d);pendingEvaluation=null;return true;
 }catch{$('engineDecision').hidden=false;$('engineDecisionText').textContent='Nästa steg kunde inte kontrolleras. Din aktuella ordination visas fortfarande. Försök igen när anslutningen fungerar.';return false}
 finally{evaluating=false}
}
$('checkNextStep').onclick=evaluateNext;

const coachDisabled=new Map();
coach=createExerciseCoach($('exerciseCoach'),{api,onDemonstrate:(frame,focus,scroll=false)=>{lesson.showFrame(frame===null?lesson.position():frame,focus);if(scroll){$('motionStudio').focus({preventScroll:true});$('motionStudio').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}},onSaved:()=>{support?.refresh();barriers?.refresh()},onBusy:value=>{
 if(value){lesson.pause();for(const b of document.querySelectorAll('#player button:not(#exerciseCoach button),[data-tab],#logout')){coachDisabled.set(b,b.disabled);b.disabled=true}}
 else{for(const [b,disabled]of coachDisabled)if(b.isConnected)b.disabled=disabled;coachDisabled.clear()}
}});
