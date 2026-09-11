/* Reda progression kernel v1. Simulation only: no network, writes or patient activation.
 * Rules and complete prescription steps are supplied by the clinician/test author.
 * These are NOT clinically validated default thresholds. No model invents a dose.
 */
(function(root){'use strict';
const VERSION='1.0.0',DAY=86400000,clone=x=>JSON.parse(JSON.stringify(x));
const messages={
 invalid:'Ramarna eller underlaget behöver korrigeras.',version:'Planen stämmer inte med den versionsbundna ramen.',
 expired:'Perioden för den här ramen är slut. Fortsatt progression behöver en ny ram.',notStarted:'Perioden har inte börjat.',
 openSession:'Avsluta det pågående passet innan nästa steg prövas.',concern:'Nya eller försämrade besvär behöver bedömas. Ingen progression föreslås.',
 requested:'Du har bett om kontakt med behandlaren.',environment:'Förutsättningarna har ändrats. Övningsvalet behöver stämmas av.',
 load:'Övrig träning belastar mer just nu. Ingen ökning föreslås.',recovery:'Återhämtningen talar för att avvakta med en ökning.',
 context:'Det behövs svar om återhämtning och annan träning.',conflict:'Registreringarna innehåller motstridiga uppgifter.',
 data:'Underlaget är ofullständigt eller har felaktiga datum.',response:'Svaret efter träningen behöver följas upp innan nästa steg kan prövas.',
 difficult:'Ett rapporterat pass möter inte villkoren för en ökning. Behåll den aktuella ordinationen medan underlaget följs upp.',
 evidence:'Fler avslutade träningsdagar med uppföljt svar behövs enligt den valda ramen.',time:'Mer tid på den här nivån behövs enligt den valda ramen.',
 ready:'Villkoren i testramen är uppfyllda. Nästa fördefinierade steg kan förhandsvisas.',
 complete:'Alla steg i ramen är prövade. En fortsatt väg behöver nya ramar; det betyder inte att rehabiliteringen är klar.'
};
function canonical(x){if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).filter(k=>x[k]!==undefined).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';return JSON.stringify(x)}
// Binding is a deterministic comparison key, not a signature or authorization proof.
function binding(plan){return canonical({schema:plan.schema,context:plan.context,goal:plan.goal,schedule:plan.schedule,exercises:plan.exercises})}
function training(plan){return canonical(plan.exercises.map(x=>({id:x.id,variantId:x.variantId,side:x.side,dose:Object.fromEntries(['sets','reps','hold','rest','tempo'].map(k=>[k,x.dose[k]])),load:x.prescribedLoad||'',range:x.prescribedRange||''})))}
function date(s){return typeof s==='string'&&/^20\d\d-\d\d-\d\d$/.test(s)&&!Number.isNaN(Date.parse(s+'T12:00:00Z'))&&new Date(s+'T12:00:00Z').toISOString().slice(0,10)===s}
function day(s){return new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Stockholm',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(s))}
function days(a,b){return (Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/DAY}
function timestamp(s){return typeof s==='string'&&/^20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?(?:Z|[+-]\d\d:\d\d)$/.test(s)&&Number.isFinite(Date.parse(s))&&date(s.slice(0,10))}
function integer(x,min,max){return Number.isInteger(x)&&x>=min&&x<=max}
function validatePlan(p){return p?.schema===6&&Array.isArray(p.exercises)&&p.exercises.length>0&&new Set(p.exercises.map(x=>x.id)).size===p.exercises.length&&p.exercises.every(x=>typeof x.id==='string'&&x.id&&typeof x.variantId==='string'&&x.variantId&&['left','right','both','simultaneous'].includes(x.side)&&[['sets',1,8],['reps',1,100],['hold',0,180],['rest',0,600],['tempo',1,60]].every(([k,min,max])=>integer(x.dose?.[k],min,max)))}
function validate(p){
 if(p?.schema!==1||p.mode!=='simulation-only'||typeof p.id!=='string'||!p.id||!integer(p.revision,1,100000))throw Error('Ramens identitet eller version saknas.');
 if(!date(p.validFrom)||!date(p.validUntil)||p.validUntil<p.validFrom)throw Error('Ange ramens giltiga start- och slutdatum.');
 const r=p.rules;if(!r||!integer(r.minSuccessfulDays,1,30)||!integer(r.minDaysAtStep,1,60)||!integer(r.maxEvidenceAgeDays,1,60)||r.minSuccessfulDays>r.maxEvidenceAgeDays)throw Error('Ange antal träningsdagar, minsta tid och underlagets giltighet.');
 if(!Array.isArray(r.acceptedEffort)||!r.acceptedEffort.length||r.acceptedEffort.some(x=>!['easy','okay'].includes(x)))throw Error('Ange vilka träningssvar som får stödja progression.');
 if(!Array.isArray(p.steps)||p.steps.length<2||p.steps.length>12||new Set(p.steps.map(x=>x.id)).size!==p.steps.length)throw Error('Ramen behöver två till tolv unika steg.');
 for(const step of p.steps)if(typeof step.id!=='string'||!step.id||typeof step.label!=='string'||!validatePlan(step.plan))throw Error('Varje steg behöver en komplett och giltig ordination.');
 const first=p.steps[0].plan;
 // A single path has one goal, environment and weekly schedule. New circumstances require a new path.
 if(p.steps.some(x=>canonical(x.plan.context)!==canonical(first.context)||x.plan.goal!==first.goal||canonical(x.plan.schedule)!==canonical(first.schedule)))throw Error('Mål, förutsättningar och veckoplan ska vara samma inom ramen.');
 if(p.steps.some((x,i)=>i>0&&training(x.plan)===training(p.steps[i-1].plan)))throw Error('Nästa steg ska beskriva en faktisk ändring.');
 return p;
}
function compile(input){return clone(validate({...clone(input),schema:1,mode:'simulation-only'}))}
function result(p,state,action,code,extra={}){return {engineVersion:VERSION,mode:'simulation-only',mayApply:false,policyId:p?.id||null,policyRevision:p?.revision||null,stepId:state?.stepId||null,action,code,message:messages[code],...extra}}
function evaluate(input={}){
 const {policy:p,plan,state,observations=[],context={},now}=input;
 const out=(action,code,extra)=>result(p,state,action,code,extra);
 try{validate(p)}catch(e){return out('blocked','invalid',{detail:e.message})}
 if(!timestamp(now)||!state||!timestamp(state.startedAt)||Date.parse(state.startedAt)>Date.parse(now)||!Array.isArray(observations))return out('blocked','data');
 const idx=p.steps.findIndex(x=>x.id===state.stepId),current=p.steps[idx],today=day(now);
 if(!current||state.policyRevision!==p.revision||!validatePlan(plan)||binding(plan)!==binding(current.plan))return out('blocked','version');
 // Requests and changed symptoms take precedence over commerce, expiry and training readiness.
 if(context.concern===true||state.reviewPending===true)return out('review','concern');
 if(context.reviewRequested===true)return out('review','requested');
 if(context.environmentChanged===true)return out('review','environment');
 // Do not infer the current step from legacy or another plan's session rows.
 if(day(state.startedAt)<p.validFrom)return out('blocked','data');
 const rows=observations.filter(x=>x?.policyId===p.id&&x.policyRevision===p.revision&&x.stepId===state.stepId),seen=new Map(),recent=[];
 for(const row of rows){
  if(typeof row.id!=='string'||!row.id||!timestamp(row.completedAt)||Date.parse(row.completedAt)>Date.parse(now))return out('blocked','data');
  if(seen.has(row.id)){if(seen.get(row.id)!==canonical(row))return out('blocked','conflict');continue}seen.set(row.id,canonical(row));
  if(Date.parse(row.completedAt)<Date.parse(state.startedAt)||days(today,day(row.completedAt))>p.rules.maxEvidenceAgeDays)continue;
  recent.push(row);
 }
 if(recent.some(row=>row.concern===true||row.function==='worse'||row.nextDay==='worse'))return out('review','concern');
 if(today>p.validUntil)return out('review','expired');
 if(today<p.validFrom)return out('wait','notStarted');
 if(context.sessionOpen===true)return out('wait','openSession');
 if(context.otherTraining==='high')return out('hold','load');
 if(context.recovery==='low')return out('hold','recovery');
 if(context.otherTraining!=='usual'||context.recovery!=='ready'||context.sessionOpen!==false||context.concern!==false||context.reviewRequested!==false||context.environmentChanged!==false)return out('wait','context');
 for(const row of recent){
  if(!['completed','partial','skipped'].includes(row.status)||!['easy','okay','heavy'].includes(row.effort)||!['controlled','difficult','unknown'].includes(row.quality)||!['stable','better','unknown'].includes(row.function)||row.concern!==false)return out('wait','data');
  if(row.status!=='completed'||!p.rules.acceptedEffort.includes(row.effort)||row.quality==='difficult')return out('hold','difficult');
  if(row.nextDay!=='settled'||row.quality==='unknown'||row.function==='unknown')return out('wait','response');
  // Next-day responses cannot be supplied ahead of the next Stockholm calendar day.
  if(!timestamp(row.respondedAt)||Date.parse(row.respondedAt)>Date.parse(now)||day(row.respondedAt)<=day(row.completedAt))return out('blocked','data');
 }
 const n=new Set(recent.map(x=>day(x.completedAt))).size,metrics={successfulDays:n,requiredDays:p.rules.minSuccessfulDays,daysAtStep:days(today,day(state.startedAt))};
 if(n<p.rules.minSuccessfulDays)return out('wait','evidence',{metrics});
 if(metrics.daysAtStep<p.rules.minDaysAtStep)return out('wait','time',{metrics});
 if(!p.steps[idx+1])return out('complete','complete',{metrics});
 const next=p.steps[idx+1];
 return out('advance','ready',{metrics,targetStepId:next.id,targetLabel:next.label,previewPlan:clone(next.plan),transitionKey:canonical([p.id,p.revision,state.stepId,state.startedAt,next.id]),evidenceIds:recent.map(x=>x.id).sort()});
}
// A future language model may explain this bounded result. It receives no authority to change it.
function explanationBrief(decision){return {engineVersion:VERSION,mode:'simulation-only',action:decision.action,reason:decision.message,allowedNextStep:decision.targetLabel||null,metrics:decision.metrics||null,restrictions:['Do not diagnose.','Do not add or change exercises, dosage, thresholds or purchase advice.','Do not claim a clinician has reviewed this result.']}}
root.RedaProgression={VERSION,compile,validate,evaluate,binding,explanationBrief,date,day};if(typeof module==='object'&&module.exports)module.exports=root.RedaProgression;
})(typeof window!=='undefined'?window:globalThis);
