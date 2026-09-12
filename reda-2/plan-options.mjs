const clone=x=>JSON.parse(JSON.stringify(x));
const stable=x=>Array.isArray(x)?x.map(stable):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])])):x;
export function optionsBinding(p){return Object.fromEntries(['schema','context','goal','schedule','exercises','clinicianNote','reviewDate','presentation','careJourney'].map(k=>[k,p[k]??null]))}
export function approvedOptions(p){
 if(!p?.planOptions)return [];
 const o=p.planOptions;
 if(o.schema!==1||o.approved!==true||JSON.stringify(stable(o.source))!==JSON.stringify(stable(optionsBinding(p)))||!Array.isArray(o.items)||o.items.length>3)throw Error('Planens alternativ behöver granskas på nytt. Kontakta behandlaren.');
 return o.items;
}
export function optionPlan(record,optionId=null){
 if(!optionId)return record;
 const p=record.payload||record,o=approvedOptions(p).find(x=>x.id===optionId);
 if(!o)throw Error('Det valda alternativet finns inte i den här planversionen.');
 const payload={...clone(p),context:clone(o.context),exercises:clone(o.exercises)};delete payload.planOptions;
 return record.payload?{...record,payload,optionId:o.id,optionLabel:o.label}:payload;
}
export function approveOptions(plan,items){
 if(!items.length||items.length>3)throw Error('Välj ett till tre alternativ.');
 const p=clone(plan);delete p.planOptions;delete p.progressionDraft;delete p.progressionFrame;
 p.planOptions={schema:1,approved:true,source:optionsBinding(p),items:items.map(x=>({id:x.id,label:x.title,reason:x.id==='less-rounds'?'time':'equipment',context:clone(x.plan.context),exercises:clone(x.plan.exercises)}))};return p;
}
export function optionUsage(plan,sessions){
 const items=approvedOptions(plan.payload||plan),rows=sessions.filter(x=>x.plan_id===plan.id&&x.completed_at&&['completed','partial'].includes(x.status));
 return [{id:null,label:'Ordinarie pass'},...items].map(o=>({id:o.id,label:o.label,total:rows.filter(s=>(s.payload?.optionId||null)===o.id).length,completed:rows.filter(s=>(s.payload?.optionId||null)===o.id&&s.status==='completed').length}));
}
