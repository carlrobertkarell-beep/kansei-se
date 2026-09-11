// Shared labels and pure, version-scoped rules. Immediate experience is never next-day evidence.
export const barriers = {
 none:'Inget särskilt', time:'Svårt att hinna', execution:'Osäker på utförandet',
 equipment:'Utrustning eller plats saknades', symptoms:'Besvären gjorde det svårt',
 energy:'Orken räckte inte', other:'Något annat'
};
export const supportLabels={no:'Nej, inte just nu',yes:'Ja, jag vill ha hjälp'};
export function normalizeReflection(input,exercises=[]){
 if(!input||typeof input!=='object'||Array.isArray(input)||Object.keys(input).some(k=>!['barrier','support','exerciseId'].includes(k)))throw Error('Kontrollera dina svar.');
 if(!Object.hasOwn(barriers,input.barrier)||!Object.hasOwn(supportLabels,input.support))throw Error('Välj vad som fungerade och om du vill ha hjälp.');
 const exerciseId=input.exerciseId||null;
 if(exerciseId!==null&&(typeof exerciseId!=='string'||!exercises.some(x=>x.id===exerciseId)))throw Error('Välj en övning från passets plan.');
 return {barrier:input.barrier,support:input.support,exerciseId};
}
export function reflectionCode(a){
 if(a.barrier==='symptoms')return 'changed_symptoms';
 if(a.barrier==='equipment')return 'changed_environment';
 if(a.barrier==='execution')return 'execution_help';
 if(['time','energy','other'].includes(a.barrier))return 'training_barrier';
 return a.support==='yes'?'requested_contact':null;
}
export function reflectionLines(row){return [barriers[row?.answers?.barrier]||'Svaret behöver kontrolleras',supportLabels[row?.answers?.support]?'Önskar hjälp: '+(row.answers.support==='yes'?'Ja':'Nej'):'',row?.exercise_name?'Gäller: '+row.exercise_name:''].filter(Boolean)}
export const dayKey=time=>new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Stockholm',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(time));
export function pendingReflections(plan,sessions=[],reflections=[],now=new Date().toISOString()){
 const answered=new Set(reflections.map(x=>x.session_id)),day=dayKey(now);
 return sessions.filter(s=>s.plan_id===plan?.id&&s.completed_at&&['completed','partial'].includes(s.status)&&dayKey(s.completed_at)===day&&!answered.has(s.id)).sort((a,b)=>Date.parse(b.completed_at)-Date.parse(a.completed_at));
}
export function todayState(plan,sessions=[],now=new Date().toISOString()){
 const day=dayKey(now),weekday=new Date(day+'T12:00:00Z').getUTCDay(),days=plan?.payload?.schedule?.days||[];
 const rows=sessions.filter(x=>x.plan_id===plan?.id),open=rows.find(x=>!x.completed_at&&['started','partial'].includes(x.status));
 const done=rows.filter(x=>x.completed_at&&dayKey(x.completed_at)===day&&['completed','partial'].includes(x.status));
 const scheduled=days.includes(weekday),next=Array.from({length:7},(_,i)=>i+1).find(n=>days.includes((weekday+n)%7));
 const nextDay=next?new Date(Date.parse(day+'T12:00:00Z')+next*86400000).toISOString().slice(0,10):null;
 if(open)return {kind:'resume',title:'Fortsätt där du slutade',detail:'Dina sparade omgångar följer med.',button:'Fortsätt passet',scheduled,nextDay,done};
 if(done.length)return {kind:'done',title:'Dagens pass är registrerat',detail:done.some(x=>x.status==='completed')?'Du har genomfört ett pass enligt din registrering.':'Du har registrerat ett delvis genomfört pass.',button:'Starta ytterligare pass',scheduled,nextDay,done};
 return {kind:scheduled?'train':'rest',title:scheduled?'Det här gör du idag':'Ingen träning planerad idag',detail:scheduled?'Följ din sparade plan, en övning i taget.':'Nästa planerade träningsdag: '+(nextDay?new Date(nextDay+'T12:00:00Z').toLocaleDateString('sv-SE',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Stockholm'}):'inte angiven')+'.',button:scheduled?'Starta passet':'Öppna pass enligt överenskommelse',scheduled,nextDay,done};
}
