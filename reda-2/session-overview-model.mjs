// Read-only projection of the current prescription and its exact session.
// This module never changes dosage, marks missing work, or advances a plan.
const feedbackLabels={light:'Lätt',okay:'Lagom',heavy:'För tungt'};
const sideLabels={left:'Vänster',right:'Höger',both:'Båda sidor',simultaneous:'Båda samtidigt'};
export function sessionOverview(exercises,session){
 const invalid={valid:false,items:[],total:0,done:0,remaining:0,completed:0,skipped:0,untouched:0,canFinish:false,allCompleted:false};
 if(!Array.isArray(exercises)||!exercises.length||!Array.isArray(session?.progress)||session.progress.length!==exercises.length)return invalid;
 const ids=new Set(),items=[];
 for(const [index,x] of exercises.entries()){
  const p=session.progress[index],sets=Number(x?.dose?.sets||1),multiplier=x?.side==='both'?2:1,total=sets*multiplier;
  if(!x?.id||ids.has(x.id)||p?.exerciseId!==x.id||!Number.isInteger(sets)||sets<1||!Number.isInteger(p.roundsDone)||p.roundsDone<0||p.roundsDone>total||!['pending','partial','completed','skipped'].includes(p.status)||(p.status==='completed'&&p.roundsDone!==total)||(p.status==='pending'&&p.roundsDone!==0))return invalid;
  ids.add(x.id);
  const done=p.roundsDone,status=p.status==='skipped'?'skipped':p.status==='completed'?'completed':done?'partial':'pending';
  const label={completed:'Alla omgångar registrerade',skipped:'Överhoppad',partial:'Delvis registrerad',pending:'Inte registrerad ännu'}[status];
  const sides=x.side==='both'?`Vänster ${Math.ceil(done/2)} av ${sets} · Höger ${Math.floor(done/2)} av ${sets}`:'';
  items.push({index,id:x.id,name:String(x.name||'Övning '+(index+1)),status,label,done,total,sides,side:sideLabels[x.side]||'',dose:String(x.dose?.label||`${sets} ${sets===1?'omgång':'omgångar'}${x.dose?.reps?' · '+x.dose.reps+' repetitioner':''}`),feedback:feedbackLabels[p.feedback]||''});
 }
 const total=items.reduce((n,x)=>n+x.total,0),done=items.reduce((n,x)=>n+x.done,0),completed=items.filter(x=>x.status==='completed').length;
 return {valid:true,items,total,done,remaining:total-done,completed,skipped:items.filter(x=>x.status==='skipped').length,untouched:items.filter(x=>x.status==='pending').length,allCompleted:completed===items.length,canFinish:!!session.id&&!session.completedAt};
}

export function hasNoRecordedRounds(rows){return Array.isArray(rows)&&rows.length>0&&rows.every(x=>Number.isInteger(x?.roundsDone)&&x.roundsDone===0)}
