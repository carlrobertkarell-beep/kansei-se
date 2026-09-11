const clone=x=>JSON.parse(JSON.stringify(x));
export const dayNames=['Söndag','Måndag','Tisdag','Onsdag','Torsdag','Fredag','Lördag'];
export const startProfiles={
 supported:{label:'Skonsamt med stöd',detail:'Låg tolerans · liten träningsvana · hemma · utan golv eller band',values:{stage:'protected',capacity:'supported',trainingHistory:'new',goalProfile:'daily',equipment:'home',floorOK:false,band:false,guidance:'guided'}},
 home:{label:'Grundträning hemma',detail:'Uppbyggnad · grundutförande · träningsvan · golv fungerar · inget band',values:{stage:'build',capacity:'standard',trainingHistory:'regular',goalProfile:'daily',equipment:'home',floorOK:true,band:false,guidance:'guided'}},
 gym:{label:'Fortsättning på gym',detail:'Uppbyggnad · hög kapacitet · genomförd grundrehab · golv och band',values:{stage:'build',capacity:'high',trainingHistory:'rehab_experienced',goalProfile:'strength',equipment:'gym',floorOK:true,band:true,guidance:'trained'}}
};
export function directionMatches(focus,blueprints){
 const groups=[[/knä|kna|patell|menisk/i,/knä|knee/i],[/axel|skuld|cuff|shoulder/i,/axel|shoulder/i],[/höft|hoft|ljumsk|gtps/i,/höft|hip/i],[/hälsena|achill|vad|fotled/i,/fotled|achill/i],[/armbåge|armbage|epicond/i,/armbåge|elbow/i],[/nack|cervik/i,/nack|neck/i],[/länd|landrygg|rygg|lumb/i,/länd|lumbar/i]];
 const tests=groups.filter(([re])=>re.test(focus||'')).map(([,re])=>re);return blueprints.filter(b=>tests.some(re=>re.test(b.name+' '+b.id)));
}
export function cleanProgression(plan){const p=clone(plan);delete p.progressionDraft;delete p.progressionFrame;return p}
export function emptyPlan(context={}){return {schema:6,context:clone(context),blueprintId:'manual',blueprintName:'Egen ordination',intelligenceTier:'foundation',patientName:context.patientName||'',goal:context.goal||'',clinicianNote:context.clinicianNote||'',presentation:context.guidance||'guided',reviewDate:context.reviewDate||'',schedule:{days:[1,3,5]},warnings:[],exercises:[],authoring:{mode:'manual',includedInVisit:false}}}
export function templateFrom(plan){
 return {schema:1,exercises:(plan.exercises||[]).map(x=>({id:x.id,variantId:x.variantId,dose:{sets:x.dose.sets,reps:x.dose.reps,hold:x.dose.hold||0,rest:x.dose.rest||0,tempo:x.dose.tempo||5}}))};
}
export function changeSummary(before,after){
 const a=before?.exercises||[],b=after.exercises||[],changes=[];
 for(const [i,x]of b.entries()){const old=a.find(y=>y.id===x.id);if(!old)changes.push('Lägg till '+x.name);else if(JSON.stringify(old)!==JSON.stringify(x))changes.push('Ändra '+x.name+': '+x.variantLabel+' · '+x.dose.label);else if(a.indexOf(old)!==i)changes.push('Flytta '+x.name)}
 for(const x of a)if(!b.some(y=>y.id===x.id))changes.push('Ta bort '+x.name);
 if(before&&JSON.stringify(before.context)!==JSON.stringify(after.context))changes.push('Uppdatera planens förutsättningar');
 return changes;
}
export function createAuthoringTools(P,D){
 const compatible=(v,c={})=>!(c.floorOK===false&&v.tags?.floor)&&!(c.band===false&&v.tags?.band)&&!(c.equipment==='home'&&v.tags?.gym)&&!(!['run','sport','hyrox'].includes(c.goalProfile)&&v.tags?.impact);
 function exercise(id,context={},variantId){const e=D.exercises.find(x=>x.id===id);if(!e)throw Error('Övningen finns inte i biblioteket.');const v=variantId?e.variants.find(v=>v.id===variantId&&compatible(v,context)):e.variants.find(v=>compatible(v,context));if(!v)throw Error('Ingen variant passar de valda förutsättningarna.');return P.exerciseFor(id,context,v.id)}
 function add(plan,id){if(plan.exercises.length>=12)throw Error('En plan kan innehålla högst 12 övningar.');if(plan.exercises.some(x=>x.id===id))throw Error('Övningen finns redan i planen. Justera sida eller dos där.');const p=cleanProgression(plan);p.exercises.push(exercise(id,p.context));return recheck(p)}
 function remove(plan,index){const p=cleanProgression(plan);p.exercises.splice(index,1);return recheck(p)}
 function move(plan,index,direction){const p=cleanProgression(plan),to=index+direction;if(to<0||to>=p.exercises.length)return p;[p.exercises[index],p.exercises[to]]=[p.exercises[to],p.exercises[index]];return p}
 function fromTemplate(template,context){const p=emptyPlan(context);for(const x of template.exercises){if(p.exercises.some(e=>e.id===x.id))throw Error('Mallen innehåller en dubblerad övning.');p.exercises.push(exercise(x.id,context,x.variantId));p.exercises[p.exercises.length-1]=P.editExercise(p,p.exercises.length-1,x.dose).exercises.at(-1)}return p}
 function recheck(plan){const p=clone(plan);p.warnings=(p.warnings||[]).filter(w=>!w.endsWith(': välj en ersättning som passar de nya förutsättningarna.'));for(const x of p.exercises){const v=D.exercises.find(e=>e.id===x.id)?.variants.find(v=>v.id===x.variantId);if(!v||!compatible(v,p.context))p.warnings.push(x.name+': välj en ersättning som passar de nya förutsättningarna.')}return p}
 function adapt(plan,changes){const p=cleanProgression(plan);p.context={...p.context,...changes};p.warnings=[];p.exercises=p.exercises.map(x=>{const e=D.exercises.find(e=>e.id===x.id),v=e?.variants.find(v=>v.id===x.variantId);if(v&&compatible(v,p.context))return x;const alternatives=(e?.variants||[]).filter(v=>compatible(v,p.context));if(!alternatives.length){p.warnings.push(x.name+': välj en ersättning som passar de nya förutsättningarna.');return x}const chosen=alternatives[0],replacement=exercise(x.id,p.context,chosen.id);if(P.allowedSides(x.id,chosen.id).includes(x.side))replacement.side=x.side;return replacement});return p}
 return {compatible,exercise,add,remove,move,fromTemplate,adapt,recheck};
}
