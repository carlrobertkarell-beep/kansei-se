const clone=x=>JSON.parse(JSON.stringify(x));const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
function stepExercise(x,stage){
 const y=clone(x),d=y.dose||{};if(stage===1&&Number.isFinite(Number(d.reps)))d.reps=clamp(Number(d.reps)+(Number(d.reps)>=10?2:1),1,100);
 if(stage===2&&Number.isFinite(Number(d.sets)))d.sets=clamp(Number(d.sets)+1,1,8);
 if(stage===3&&Number.isFinite(Number(d.reps)))d.reps=clamp(Number(d.reps)+(Number(d.reps)>=10?2:1),1,100);
 y.dose=d;return y;
}
export function prepareCorridor(plan,{steps=4}={}){
 if(!plan?.payload?.exercises?.length)return {valid:false,steps:[]};
 const out=[{label:'Nuvarande ordination',prescription:clone(plan.payload.exercises),kind:'current'}];let current=clone(plan.payload.exercises);
 for(let i=1;i<steps;i++){current=current.map(x=>stepExercise(x,i));out.push({label:i===1?'Öka repetitionsdos':i===2?'Öka antal omgångar':'Nästa dossteg',prescription:clone(current),kind:'dose'})}
 return {valid:true,steps:out};
}
export function corridorDiff(a,b){return (b||[]).map((x,i)=>{const old=(a||[])[i];return {id:x.id,name:x.name,changed:JSON.stringify(old?.dose)!==JSON.stringify(x.dose)||old?.variantId!==x.variantId||old?.side!==x.side,before:old?.dose||null,after:x.dose||null}}).filter(x=>x.changed)}
