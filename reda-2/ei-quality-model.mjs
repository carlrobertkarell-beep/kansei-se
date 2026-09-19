const pct=(n,d)=>d?Math.round(n/d*1000)/10:0;
export function eiQuality(decisions=[],reviews=[],cases=[]){
 const out={total:decisions.length,advance:0,hold:0,regress:0,escalate:0,applied:0,reviewed:0,overridden:0,postChangeCases:0};
 const reviewBy=new Map(reviews.map(r=>[r.decision_id,r]));
 for(const d of decisions){const a=d.action==='review'?'escalate':d.action;if(Object.hasOwn(out,a))out[a]++;if(d.applied)out.applied++;const r=reviewBy.get(d.id);if(r){out.reviewed++;if(['reject','override','changed'].includes(r.verdict))out.overridden++}if(d.applied&&d.result_plan_id&&cases.some(c=>c.plan_id===d.result_plan_id&&Date.parse(c.created_at)>=Date.parse(d.created_at)))out.postChangeCases++}
 return {...out,overrideRate:pct(out.overridden,out.reviewed),postChangeCaseRate:pct(out.postChangeCases,out.applied)};
}
export function qualityByBlueprint(decisions=[]){const m=new Map();for(const d of decisions){const k=d.blueprint_id||'unknown',x=m.get(k)||{blueprint:k,total:0,advance:0,hold:0,regress:0,escalate:0};x.total++;const a=d.action==='review'?'escalate':d.action;if(Object.hasOwn(x,a))x[a]++;m.set(k,x)}return [...m.values()].sort((a,b)=>b.total-a.total||a.blueprint.localeCompare(b.blueprint))}
