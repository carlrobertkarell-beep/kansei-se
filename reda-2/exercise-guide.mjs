import {createMovementLesson} from './movement-lesson.mjs?v=1';
import {createExerciseCoach} from './exercise-coach.mjs?v=20260912-coach1';
import {sideLabels,helpSummary} from './exercise-help-model.mjs?v=20260912-coach1';
const $=id=>document.getElementById(id),F=window.RedaFigures;
const examples=[
 {id:'chair',name:'Uppresning från stol',motionKey:'sit-to-stand.support',side:'simultaneous',support:'Stol med armstöd',instructions:['Placera fötterna stadigt framför stolen.','Luta överkroppen framåt och res dig med handstöd.','Sätt dig tillbaka kontrollerat.']},
 {id:'extension',name:'Benspark från stol',motionKey:'knee-extension.seated',side:'left',support:'Stol med ryggstöd',instructions:['Sitt med låret kvar mot stolen.','Sträck underbenet enligt rörelseomfånget i din plan.','Återgå till startläget.']},
 {id:'calf',name:'Tåhävning',motionKey:'calf-raise.bilateral',side:'simultaneous',support:'Stabilt handstöd framför kroppen',instructions:['Placera båda fötterna på golvet och ta stöd med händerna.','Lyft hälarna med framfoten kvar i golvet.','Sänk hälarna kontrollerat.']},
 {id:'bridge',name:'Höftlyft',motionKey:'bridge.bilateral',side:'simultaneous',support:'Matta på golvet',instructions:['Ligg på rygg med böjda knän och fötterna mot underlaget.','Lyft bäckenet enligt instruktionen i din plan.','Sänk tillbaka med skuldror och fötter kvar mot underlaget.']},
 {id:'step',name:'Step-up med stöd',motionKey:'step-up.supported',side:'left',support:'Stabilt steg och handstöd',instructions:['Placera den sida du tränar på steget.','Kliv upp med handstöd.','Återgå kontrollerat till startläget.']}
].map(x=>({...x,equipment:x.support,prescribedRange:'Följ det rörelseomfång du och behandlaren har gått igenom.',dose:{sets:2,reps:8,hold:0,rest:45,label:'Fiktivt exempel: 2 omgångar × 8 repetitioner'}}));
let current=examples[0];
const lesson=createMovementLesson($('movementLesson'),{onReady:()=>{const host=$('guideResult');host.hidden=false;host.textContent='I patientens plan kommer du nu till dina omgångar. Ingen träning registreras av att titta på guiden.';host.scrollIntoView({block:'center',behavior:'smooth'})}});
const coach=createExerciseCoach($('exerciseCoach'),{preview:true,api:{submitExerciseHelp:async(session,id,rid,body)=>{const h={id:rid,...body,exercise:current,exercise_name:current.name,plan_version:1,option_label:'Fiktivt exempel'};return h}},onSaved:h=>{
 const host=$('guideResult');host.hidden=false;host.replaceChildren();const title=document.createElement('h3');title.textContent=h.outcome==='clear'?'Så skulle din återkoppling registreras':'Så skulle underlaget visas för behandlaren';host.append(title);const list=document.createElement('ul');for(const line of helpSummary(h)){const li=document.createElement('li');li.textContent=line;list.append(li)}host.append(list);
},onDemonstrate:(t,f,scroll)=>{lesson.showFrame(t===null?lesson.position():t,f);if(scroll)$('motionStudio').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}});
function choose(){lesson.pause();current={...examples[Number($('guideExercise').value)]};const bilateral=current.side==='simultaneous';$('guideSide').disabled=bilateral;if(!bilateral)current.side=$('guideSide').value;$('exName').textContent=current.name;$('dose').textContent=current.dose.label;$('guideResult').hidden=true;lesson.setExercise(current,{exerciseSide:current.side,contextId:'preview'});coach.setExercise({plan:{id:'example-'+current.id+'-'+current.side,version:1},exercise:current,sessionId:'preview'});}
$('guideExercise').innerHTML=examples.map((x,i)=>`<option value="${i}">${x.name}</option>`).join('');$('guideExercise').onchange=choose;$('guideSide').onchange=choose;
choose();
