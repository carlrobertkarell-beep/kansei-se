/* Read-only review of loaded sessions. Never modifies a plan or suggests progression. */
(function(root){'use strict';
const day=ts=>{const d=new Date(ts);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Stockholm',year:'numeric',month:'2-digit',day:'2-digit'}).format(d):null};
const shift=(d,n)=>new Date(Date.parse(d+'T12:00:00Z')+n*86400000).toISOString().slice(0,10);
function build({plans=[],sessions=[],planId,now=new Date().toISOString(),limit=30}){
 const published=plans.filter(p=>p.status!=='draft'&&p.activated_at),plan=published.find(p=>p.id===planId)||published.find(p=>p.status==='active')||published[0];
 if(!plan)return null;
 const today=day(now),activated=day(plan.activated_at),next=published.filter(p=>Date.parse(p.activated_at)>Date.parse(plan.activated_at)).sort((a,b)=>Date.parse(a.activated_at)-Date.parse(b.activated_at))[0];
 // Complete calendar days only, to avoid calling a part-day activation or today a missed day.
 const end=next&&day(next.activated_at)<today?day(next.activated_at):today,start=[shift(end,-14),shift(activated,1)].sort().at(-1);
 const matches=s=>s.plan_id?s.plan_id===plan.id:s.plan_version===plan.version;
 const rows=sessions.filter(s=>matches(s)&&day(s.started_at)&&day(s.started_at)>=start&&day(s.started_at)<end);
 const schedule=plan.payload?.schedule?.days,hasSchedule=Array.isArray(schedule)&&schedule.length>0&&schedule.every(n=>Number.isInteger(n)&&n>=0&&n<=6);
 const scheduled=[];if(hasSchedule)for(let d=start;d<end;d=shift(d,1))if(schedule.includes(new Date(d+'T12:00:00Z').getUTCDay()))scheduled.push(d);
 const dates=sessions.map(s=>day(s.started_at)).filter(Boolean).sort(),limited=sessions.length>=limit&&(!dates[0]||dates[0]>=start);
 const done=rows.filter(s=>s.status==='completed'),doneDays=new Set(done.map(s=>day(s.started_at))),fulfilled=scheduled.filter(d=>doneDays.has(d)).length;
 const exercises=new Map((plan.payload?.exercises||[]).map(x=>[x.id,{id:x.id,name:x.name,variant:x.variantLabel||'',dose:x.dose?.label||'',completed:0,partial:0,skipped:0,heavy:0,easy:0,okay:0}]));
 for(const s of rows)for(const x of s.payload?.exercises||[]){if(!exercises.has(x.exerciseId))exercises.set(x.exerciseId,{id:x.exerciseId,name:'Övning utan namn i denna plan',variant:'',dose:'',completed:0,partial:0,skipped:0,heavy:0,easy:0,okay:0});const r=exercises.get(x.exerciseId);if(['completed','partial','skipped'].includes(x.status))r[x.status]++;if(['heavy','easy','okay'].includes(x.feedback))r[x.feedback]++}
 return {plan,start,end,limited,hasSchedule,scheduled:scheduled.length,fulfilled,trainingDays:doneDays.size,unplannedDays:[...doneDays].filter(d=>!scheduled.includes(d)).length,completed:done.length,partial:rows.filter(s=>['partial','started'].includes(s.status)).length,rows,exercises:[...exercises.values()],todaySessions:sessions.filter(s=>matches(s)&&day(s.started_at)===today).length,emptyPeriod:start>=end};
}
root.RedaFollowup={build,day,shift};if(typeof module==='object'&&module.exports)module.exports=root.RedaFollowup;
})(typeof window!=='undefined'?window:globalThis);
