/* Minimal, account-scoped outbox. No names, email addresses or plan contents. */
(function(root){'use strict';
const prefix='reda:pending-session:v1:';
function valid(s,plan){
 const xs=plan?.payload?.exercises||[];
 return !!s&&typeof s.id==='string'&&Number.isFinite(Date.parse(s.startedAt))&&['started','partial','completed'].includes(s.status)&&Array.isArray(s.progress)&&s.progress.length===xs.length&&s.progress.every((p,i)=>p.exerciseId===xs[i].id&&Number.isInteger(p.roundsDone)&&p.roundsDone>=0&&p.roundsDone<=root.RedaSession.rounds(xs[i]).length&&p.totalRounds===root.RedaSession.rounds(xs[i]).length&&['pending','partial','completed','skipped'].includes(p.status)&&[null,'light','okay','heavy'].includes(p.feedback??null));
}
function fromRow(row,plan){
 const saved=row?.payload?.exercises;
 if(!row||row.completed_at||row.plan_id!==plan.id||row.plan_version!==plan.version||!Array.isArray(saved)||saved.length!==plan.payload.exercises.length||new Set(saved.map(x=>x.exerciseId)).size!==saved.length)return null;
 const s=root.RedaSession.create(plan.payload.exercises,row.client_session_id,row.started_at);
 s.status=row.status;s.progress=s.progress.map(p=>({...p,...saved.find(x=>x.exerciseId===p.exerciseId),totalRounds:p.totalRounds}));
 return valid(s,plan)?s:null;
}
function read(storage,userId){try{return JSON.parse(storage.getItem(prefix+userId)||'null')}catch{return null}}
function write(storage,userId,plan,s,index){try{storage.setItem(prefix+userId,JSON.stringify({planId:plan.id,planVersion:plan.version,session:s,index,updatedAt:new Date().toISOString()}));return true}catch{return false}}
function clear(storage,userId){try{storage.removeItem(prefix+userId)}catch{}}
function previous(row,pending){
 if(pending?.session){const s=pending.session;return {planId:pending.planId,clientSessionId:s.id,startedAt:s.startedAt,payload:{exercises:s.progress.map(p=>({exerciseId:p.exerciseId,status:p.status,roundsDone:p.roundsDone,feedback:p.feedback}))}}}
 return {planId:row.plan_id,clientSessionId:row.client_session_id,startedAt:row.started_at,payload:row.payload};
}
function choose(plan,rows,pending){
 if(pending?.session&&rows.some(r=>r.client_session_id===pending.session.id&&r.completed_at))return {...choose(plan,rows,null),discard:true};
 if(pending?.session&&pending.planId===plan.id&&pending.planVersion===plan.version&&valid(pending.session,plan)){
  const server=rows.find(r=>r.client_session_id===pending.session.id);
  if(server?.completed_at)return {session:null,index:0,discard:true};
  return {session:pending.session,index:Math.min(Math.max(0,pending.index||0),plan.payload.exercises.length-1),retry:true};
 }
 if(pending?.session&&!Array.isArray(pending.session.progress))return {blocked:true,message:'Lokalt sparat pass kunde inte läsas. Kontakta kliniken.'};
 if(pending?.session)return {blocked:true,previous:previous(null,pending),message:'En ny plan finns. Spara och avsluta det föregående passet med dina markerade omgångar innan du börjar den nya planen.'};
 const open=rows.find(r=>!r.completed_at&&['started','partial'].includes(r.status));
 if(!open)return {session:null,index:0};
 if(open.plan_id!==plan.id||open.plan_version!==plan.version)return {blocked:true,previous:previous(open,null),message:'En ny plan finns. Avsluta det föregående passet med de omgångar du redan har markerat innan du börjar den nya planen.'};
 const s=fromRow(open,plan);
 if(!s)return {blocked:true,message:'Det påbörjade passet kunde inte återställas säkert. Kontakta kliniken.'};
 const i=s.progress.findIndex(p=>!['completed','skipped'].includes(p.status));
 return {session:s,index:i<0?s.progress.length-1:i};
}
root.RedaRecovery={valid,fromRow,read,write,clear,choose};
})(typeof window!=='undefined'?window:globalThis);
