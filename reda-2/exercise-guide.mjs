import {createPatientAccount} from './patient-account.mjs?v=2';
import {createMovementLesson} from './movement-lesson.mjs?v=5';
import {mountExercisePlayer} from './exercise-player.mjs?v=2';
import {createExercisePreview,renderExerciseOverview,renderPreparation,doseText} from './patient-journey.mjs?v=4';
import {createExerciseCoach} from './exercise-coach.mjs?v=20260912-coach1';
import {helpSummary} from './exercise-help-model.mjs?v=20260912-coach1';
const $=id=>document.getElementById(id),S=window.RedaSession;
const exercises=[
 {id:'chair',name:'Uppresning från stol',motionKey:'sit-to-stand.support',side:'simultaneous',support:'Stol med armstöd',why:'För att göra det lättare att komma upp från en stol i vardagen.',instructions:['Placera fötterna stadigt framför stolen.','Luta överkroppen framåt och res dig med handstöd.','Sätt dig tillbaka kontrollerat.']},
 {id:'extension',name:'Benspark från stol',motionKey:'knee-extension.seated',side:'left',support:'Stol med ryggstöd',why:'För att träna framsidan av låret med stöd från stolen.',instructions:['Sitt med låret kvar mot stolen.','Sträck underbenet enligt rörelseomfånget i din plan.','Återgå till startläget.']},
 {id:'calf',name:'Tåhävning',motionKey:'calf-raise.bilateral',side:'simultaneous',support:'Stabilt handstöd',why:'För att träna vaderna i stående med ett stabilt stöd.',instructions:['Placera båda fötterna på golvet och ta stöd med händerna.','Lyft hälarna med framfoten kvar i golvet.','Sänk hälarna kontrollerat.']}
].map(x=>({...x,equipment:x.support,prescribedRange:'Följ det rörelseomfång du och behandlaren har gått igenom.',dose:{sets:2,reps:8,hold:0,rest:45,label:'2 omgångar · 8 repetitioner'}}));
let session=null,index=0,finished=false,reflection=null,finalizing=false;const history=new Map();let historyFilter='all';
const accountUI=createPatientAccount({header:document.querySelector('.patient-app>.top'),preview:true,onExerciseHelp:()=>{tab('program');$('programExercises').querySelector('button')?.focus({preventScroll:true})}});
const preview=createExercisePreview(),lesson=createMovementLesson($('movementLesson')),shell=mountExercisePlayer($('player'),{lesson,preview:true,isBusy:()=>demoBusy()});
const current=()=>exercises[index];
function updateHistory(){
 if(!session)return;
 const done=session.progress.filter(p=>p.status==='completed').length;
 history.set(session.id,{time:session.completedAt||session.startedAt,title:finished?(done===exercises.length?'Pass genomfört':'Pass delvis genomfört'):'Påbörjat pass',detail:done+' av '+exercises.length+' övningar genomförda',reflection});renderLog();
}
function renderLog(){
 const host=$('demoLog');host.replaceChildren();
 const rows=historyFilter==='plans'?[]:[...history.values()].reverse();
 for(const e of rows){const li=document.createElement('li'),time=document.createElement('time'),title=document.createElement('strong'),detail=document.createElement('p');time.dateTime=e.time;time.textContent=new Date(e.time).toLocaleString('sv-SE',{timeZone:'Europe/Stockholm',day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'});title.textContent=e.title;detail.textContent=e.detail;li.append(time,title,detail);
 if(e.reflection){const answer=document.createElement('p');answer.className='history-answer';answer.textContent={none:'Inget särskilt gjorde passet svårt',execution:'Utförandet kändes oklart',symptoms:'Besvären gjorde passet svårt',time:'Svårt att hinna',equipment:'Utrustningen gjorde passet svårt'}[e.reflection];li.append(answer)}host.append(li)}
 $('historyEmpty').hidden=!!rows.length;$('historyEmpty').textContent=historyFilter==='plans'?'Inga planändringar i exemplet. Här visas ändringar när din behandlare uppdaterar planen.':'Inga pass ännu. När du börjar träna samlas varje pass här.';
}
const coach=createExerciseCoach($('exerciseCoach'),{preview:true,api:{submitExerciseHelp:async(s,id,rid,body)=>({id:rid,...body,exercise:current(),exercise_name:current().name,plan_version:1,option_label:'Fiktivt exempel'})},onSaved:h=>{
 const host=$('guideResult');host.hidden=false;host.replaceChildren();const title=document.createElement('h3');title.textContent=h.outcome==='clear'?'Så skulle din återkoppling registreras':'Så skulle underlaget visas för behandlaren';host.append(title);const list=document.createElement('ul');for(const line of helpSummary(h)){const li=document.createElement('li');li.textContent=line;list.append(li)}host.append(list);
},onDemonstrate:(t,f,scroll)=>{lesson.showFrame(t===null?lesson.position():t,f);if(scroll){shell.closePanels();$('motionStudio').focus()}},onBusy:lockDemo});
function tab(name){lesson.pause();document.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===name);if(b.dataset.tab===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('hidden',t.id!==name));window.scrollTo(0,0)}
function home(){
 const onPreview=x=>preview.open(x,{contextId:'example-plan-1'});
 renderExerciseOverview($('todayExercises'),{exercises,progress:session?.progress||[],onPreview});renderExerciseOverview($('programExercises'),{exercises,progress:session?.progress||[],onPreview});renderPreparation($('todayPreparation'),exercises);
 $('start').textContent=finished?'Prova passet igen':session?'Fortsätt passet':'Starta passet';$('todayTitle').textContent=finished?'Dagens pass är registrerat':session?'Fortsätt där du slutade':'Dagens träning';$('todayCard').dataset.dayState=finished?'done':session?'resume':'train';$('todayDetail').textContent=finished?'Du kan se dina markeringar och öppna övningarna igen.':session?'Dina markeringar finns kvar medan du provar exemplet.':'I din takt, en övning i taget.';
 $('followTitle').textContent=finished?(session.status==='completed'?'Du har provat ett helt pass.':'Du har avslutat ett delvis genomfört pass.'):'Inget avslutat pass i exemplet.';$('followDetail').textContent=reflection?'Du har lämnat återkoppling i exemplet. Inget har skickats.':finished?'Berätta vad som fungerade och vad som blev svårt.':'När du avslutar passet kan du lämna återkoppling.';$('followAction').textContent=finished&&!reflection?'Berätta hur det gick':'Till dagens plan';
}
function demoBusy(){return finalizing||coach.isBusy()}
const demoLocked=new Map();
function lockDemo(value){
 if(value){lesson.pause();for(const b of document.querySelectorAll('#player button:not(#exerciseCoach button),[data-tab],#start')){demoLocked.set(b,b.disabled);b.disabled=true}}
 else{for(const [b,disabled]of demoLocked)if(b.isConnected)b.disabled=disabled;demoLocked.clear()}
 $('player').setAttribute('aria-busy',String(value));
}
function render(){
 const x=current(),p=session.progress[index],rounds=S.rounds(x),active=rounds[Math.min(p.roundsDone,rounds.length-1)];
 $('player').dataset.complete=String(p.status==='completed'||p.status==='skipped');$('pos').textContent=(index+1)+' av '+exercises.length;
 const done=session.progress.reduce((n,p)=>n+p.roundsDone,0),total=session.progress.reduce((n,p)=>n+p.totalRounds,0);$('sessionProgressText').textContent=done+' av '+total+' omgångar registrerade';$('sessionProgress').max=total;$('sessionProgress').value=done;
 $('playerCurrentRound').textContent=p.status==='skipped'?'Överhoppad · '+p.roundsDone+' av '+rounds.length+' omgångar klara':p.status==='completed'?(rounds.length===1?'Övningen är klar':'Alla '+rounds.length+' omgångar klara'):'Omgång '+Math.min(rounds.length,p.roundsDone+1)+' av '+rounds.length;
 $('exName').textContent=x.name;$('dose').textContent=doseText(x);$('next').textContent=index===exercises.length-1?'Avsluta pass':'Nästa övning';$('next').disabled=!['completed','skipped'].includes(p.status);$('rounds').replaceChildren();
 rounds.forEach((r,i)=>{const b=document.createElement('button');b.className='round';b.type='button';b.dataset.round=String(i);b.disabled=i!==p.roundsDone||p.status==='skipped';b.textContent='Omgång '+r.set+' klar'+(r.side==='left'?' · vänster':r.side==='right'?' · höger':'');b.onclick=()=>{if(demoBusy()||finished||i!==session.progress[index].roundsDone||session.progress[index].status==='skipped')return;session=S.mark(session,index,i);render();if(session.progress[index].roundsDone<rounds.length)shell.startRest(x.dose.rest)};$('rounds').append(b)});
 lesson.setExercise(x,{exerciseSide:active?.side||x.side,contextId:'example-plan-1'});coach.setExercise({plan:{id:'example-plan-1',version:1},exercise:x,sessionId:session.id});
 document.querySelectorAll('[data-effort]').forEach(b=>{b.setAttribute('aria-pressed',String(p.feedback===b.dataset.effort));b.onclick=()=>{if(demoBusy()||finished)return;p.feedback=b.dataset.effort;render()}});
 shell.updateActions({exercise:x,progress:p,index,rows:session.progress});$('playerSaveStatus').textContent='Exempel · inga uppgifter sparas';
}
function changeProgress(change){if(!session||finished||demoBusy())return;shell.endRest();shell.closePanels();session=change(session);render();updateHistory();($('rounds').querySelector('button:not(:disabled)')||$('next')).focus({preventScroll:true})}
function moveExercise(nextIndex){if(!session||finished||demoBusy()||nextIndex<0||nextIndex>=exercises.length)return;lesson.pause();shell.endRest();shell.closePanels();index=nextIndex;$('guideResult').hidden=true;render();updateHistory();$('exName').focus({preventScroll:true})}
function finish(){
 if(!session||finished||demoBusy())return;finalizing=true;lesson.pause();shell.endRest();shell.closePanels();session=S.finish(session,new Date().toISOString());finished=true;
 leave();$('todayCard').hidden=true;$('careNote').hidden=true;$('journeyFinish').hidden=false;
 const done=session.progress.filter(p=>p.status==='completed').length,rounds=session.progress.reduce((n,p)=>n+p.roundsDone,0);$('journeyFinish').querySelector('h2').textContent=session.status==='completed'?'Passet är klart.':'Ditt pass är avslutat.';$('finishDetail').textContent=done+' av '+exercises.length+' övningar och '+rounds+' '+(rounds===1?'omgång':'omgångar')+' markerade som genomförda. Berätta gärna hur det fungerade.';
 updateHistory();finalizing=false;$('journeyFinish').querySelector('h2').focus({preventScroll:true});
}
function leave(){updateHistory();lesson.pause();shell.closePanels();$('app').dataset.playerOpen='false';$('player').classList.add('hidden');home();window.scrollTo(0,0)}
function returnHome(){if(demoBusy())return;leave();$('todayCard').hidden=false;$('careNote').hidden=false;$('journeyFinish').hidden=true;$('demoReflection').hidden=true;tab('today');$('start').focus({preventScroll:true})}
function reflect(){leave();tab('today');$('todayCard').hidden=true;$('careNote').hidden=true;$('journeyFinish').hidden=true;$('demoReflection').hidden=false;$('demoReflection').querySelector('button').focus({preventScroll:true})}
$('start').onclick=()=>{if(demoBusy())return;preview.close();if(!session||finished){session=S.create(exercises,crypto.randomUUID(),new Date().toISOString());index=0;finished=false;reflection=null;updateHistory();$('demoReflectionAnswer').hidden=true;$('doneReflection').hidden=true;document.querySelectorAll('[data-barrier]').forEach(b=>b.removeAttribute('aria-pressed'))}tab('today');$('journeyFinish').hidden=true;$('demoReflection').hidden=true;$('app').dataset.playerOpen='true';$('player').classList.remove('hidden');render();$('exName').focus({preventScroll:true});window.scrollTo(0,0)};
$('next').onclick=()=>{if($('next').disabled||demoBusy()||finished)return;if(index<exercises.length-1){moveExercise(index+1);return}finish()};
$('skip').onclick=()=>{if(session?.progress[index]?.roundsDone>=session?.progress[index]?.totalRounds)return;changeProgress(s=>S.skip(s,index))};
$('undoRound').onclick=()=>{if(session?.progress[index]?.roundsDone)changeProgress(s=>S.undo(s,index))};
$('resumeSkipped').onclick=()=>{if(session?.progress[index]?.status==='skipped')changeProgress(s=>S.resume(s,index))};
$('previousExercise').onclick=()=>moveExercise(index-1);$('confirmFinish').onclick=finish;
$('closePlayer').onclick=returnHome;$('returnToday').onclick=returnHome;$('showReflection').onclick=reflect;$('doneReflection').onclick=returnHome;$('followAction').onclick=()=>finished&&!reflection?reflect():returnHome();$('previewFirst').onclick=()=>preview.open(exercises[0],{contextId:'example-plan-1'});
for(const b of document.querySelectorAll('[data-tab]'))b.onclick=()=>{if(demoBusy())return;preview.close();if(b.dataset.tab==='today'){returnHome();return}tab(b.dataset.tab)};
for(const b of document.querySelectorAll('[data-barrier]'))b.onclick=()=>{reflection=b.dataset.barrier;document.querySelectorAll('[data-barrier]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));$('demoReflectionAnswer').hidden=false;$('doneReflection').hidden=false;$('demoReflectionAnswer').textContent=reflection==='none'?'I din egen plan sparas svaret som underlag för uppföljningen. I det här exemplet skickas inget.':reflection==='execution'?'Nästa steg är hjälp med den övning som var oklar. I din egen plan följer övning och planversion med till behandlaren när du ber om hjälp.':reflection==='symptoms'?'Förändrade besvär behöver bedömas av din behandlare. I det här exemplet skickas inget meddelande.':'I din egen plan kan uppföljningen hjälpa dig att hitta vad som fungerar i din vardag. Här provar du bara återkopplingen.';updateHistory();home()};
for(const b of document.querySelectorAll('[data-demo-history]'))b.onclick=()=>{historyFilter=b.dataset.demoHistory;document.querySelectorAll('[data-demo-history]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));renderLog()};
home();renderLog();
