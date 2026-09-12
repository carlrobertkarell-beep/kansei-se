import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {emptyPlan,createAuthoringTools} from '../../reda-2/plan-authoring-model.mjs';
import {adaptationOptions,changedPrescriptions,roundCount,supportFor,prescriptionFacts,adaptationRequest,verifyAdaptation} from '../../reda-2/everyday-support.mjs';
const ctx={console};ctx.window=ctx;ctx.globalThis=ctx;vm.createContext(ctx);
for(const f of ['data.js','clinical-model-v2.js','clinical-addons.js','clinical-library-v3.js','exercise-intelligence-knee.js','exercise-intelligence-next.js','exercise-quality.js','core.js','planner.js'])vm.runInContext(fs.readFileSync('reda-2/'+f,'utf8'),ctx);
const P=ctx.RedaPlanner,D=ctx.RedaData,T=createAuthoringTools(P,D);
const plan=()=>P.editExercise(T.add(T.add(emptyPlan({floorOK:true,band:true,equipment:'gym'}),'chair'),'extension'),1,{sets:3,side:'left',reps:7,prescribedLoad:'Individuell vikt',prescribedRange:'Individuellt omfång'});
test('time proposal preserves every exercise, side, rep, rest, load and range; never mutates the active plan',()=>{
 const p=plan();p.progressionDraft={old:true};const original=JSON.stringify(p),[option]=adaptationOptions(P,D,p,'time');
 assert.equal(JSON.stringify(p),original);assert.equal(option.plan.progressionDraft,undefined);
 assert.equal(option.plan.exercises.length,p.exercises.length);assert.ok(roundCount(option.plan)<roundCount(p));
 option.plan.exercises.forEach((x,i)=>{const old=p.exercises[i];assert.equal(x.dose.sets,Math.max(1,old.dose.sets-1));for(const key of ['reps','rest','hold','tempo'])assert.equal(x.dose[key],old.dose[key]);for(const key of ['side','variantId','prescribedLoad','prescribedRange'])assert.equal(x[key],old[key]);assert.equal(JSON.stringify(x.instructions),JSON.stringify(old.instructions))});
 assert.ok(changedPrescriptions(p,option.plan).every(x=>x.fields.length===1&&x.fields[0].label==='Dos'));
});
test('symptoms and energy do not produce autonomous dosage proposals; already minimal plans stay minimal',()=>{
 const p=plan();assert.equal(adaptationOptions(P,D,p,'symptoms').length,0);assert.equal(adaptationOptions(P,D,p,'energy').length,0);
 let single=P.editExercise(T.add(emptyPlan(),'extension'),0,{sets:1});assert.equal(adaptationOptions(P,D,single,'time').length,0);
 assert.equal(supportFor({barrier:'symptoms',support:'no'}).action,'contact');assert.equal(supportFor({barrier:'execution',support:'no'}).action,'guide');
 assert.equal(supportFor({barrier:'none',support:'yes'}).action,'contact');
});
test('equipment alternatives preserve unresolved exercises and prior warnings instead of declaring completion',()=>{
 const p=T.add(plan(),'bridge');p.warnings=['Klinisk uppgift behöver kompletteras'];const x=adaptationOptions(P,D,p,'equipment').find(x=>x.id==='floor');
 assert.ok(x.plan.exercises.some(e=>e.id==='bridge'));assert.ok(x.plan.warnings.some(w=>w.includes('ersättning')));assert.ok(x.plan.warnings.includes(p.warnings[0]));
});
test('guide facts use individual prescription, preserve zero rest, and omit absent information',()=>{
 const x={...plan().exercises[1],dose:{label:'Min ordination',rest:0}};const facts=new Map(prescriptionFacts(x));assert.equal(facts.get('Ordinerad belastning'),'Individuell vikt');assert.equal(facts.get('Sida'),'Vänster');assert.equal(facts.get('Vila mellan omgångar'),'0 sekunder');assert.equal(prescriptionFacts({}).length,0);
});
const detail=()=>({patient:{patient_id:'patient-a',plan_id:'plan-a',plan_version:3},token:'snapshot-a',cases:[{id:'case-a',code:'training_barrier',reflection:{id:'reflection-a',plan_id:'plan-a',plan_version:3,answers:{barrier:'time',support:'no'}}}]});
const active={id:'plan-a',version:3,status:'active'};
test('adaptation carries exact patient, version and evidence; changed evidence or newer draft blocks reuse',()=>{
 const d=detail(),request=adaptationRequest(d);assert.equal(verifyAdaptation(request,d,active).id,'reflection-a');
 for(const changed of [{...d,token:'new'}, {...d,patient:{...d.patient,patient_id:'other'}},{...d,cases:[]},{...d,cases:[...d.cases,{code:'changed_symptoms'}]}])assert.throws(()=>verifyAdaptation(request,changed,active));
 assert.throws(()=>verifyAdaptation(request,d,{id:'new-draft',version:4,status:'draft'}),/utkast/);
});
test('historical reflections and clinical symptom flags cannot offer a quick adaptation',()=>{
 const d=detail();d.cases[0].reflection.plan_id='old-plan';assert.equal(adaptationRequest(d),null);const symptoms=detail();symptoms.cases.push({code:'changed_symptoms'});assert.equal(adaptationRequest(symptoms),null);
});
