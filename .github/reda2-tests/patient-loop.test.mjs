import test from 'node:test';
import assert from 'node:assert/strict';
import {todayState,pendingReflections,normalizeReflection,reflectionCode} from '../../reda-2/patient-loop.mjs';
import {propose} from '../../reda-2/engine/clinic-proposals.mjs';
const now='2026-09-11T12:00:00Z',plan={id:'current',payload:{schedule:{days:[1,3,5]},exercises:[{id:'chair'}]}};
const session={id:'s1',plan_id:'current',status:'completed',started_at:now,completed_at:now};
test('today follows Stockholm schedule, old versions do not complete the current day',()=>{
 assert.equal(todayState(plan,[],now).kind,'train');
 assert.equal(todayState(plan,[],'2026-09-12T10:00:00Z').kind,'rest');
 assert.equal(todayState(plan,[{...session,plan_id:'old'}],now).kind,'train');
 assert.equal(todayState(plan,[session],now).kind,'done');
 assert.equal(todayState(plan,[{...session,status:'partial',completed_at:null}],now).kind,'resume');
 assert.equal(todayState(plan,[],'2026-09-11T22:01:00Z').kind,'rest');
});
test('immediate questions only offer todays closed current-version sessions and disappear after a receipt',()=>{
 assert.equal(pendingReflections(plan,[session],[],now).length,1);
 assert.equal(pendingReflections(plan,[session],[{session_id:'s1'}],now).length,0);
 assert.equal(pendingReflections(plan,[session],[],'2026-09-12T10:00:00Z').length,0);
 assert.equal(pendingReflections(plan,[{...session,completed_at:null}],[],now).length,0);
 assert.equal(pendingReflections(plan,[{...session,plan_id:'old'}],[],now).length,0);
});
test('explicit answers bind to an actual exercise and never invent next-day recovery',()=>{
 const input=normalizeReflection({barrier:'time',support:'no',exerciseId:'chair'},plan.payload.exercises);
 assert.deepEqual(input,{barrier:'time',support:'no',exerciseId:'chair'});
 assert.equal(reflectionCode(input),'training_barrier');assert.equal(reflectionCode({barrier:'none',support:'no'}),null);
 assert.throws(()=>normalizeReflection({...input,exerciseId:'foreign'},plan.payload.exercises));
 assert.throws(()=>normalizeReflection({...input,nextDay:'settled'},plan.payload.exercises));
 assert.throws(()=>normalizeReflection({...input,support:'unknown'},plan.payload.exercises));
});
const data={today:'2026-09-11',patient:{patient_status:'active',connected:true,plan_id:'current'},cases:[{code:'training_barrier',status:'open',created_at:now,reflection:{plan_version:2,answers:{barrier:'time',support:'no'},exercise_name:'Uppresning'}}]};
test('EI proposes concrete routine support with provenance, never changes the prescription',()=>{
 const p=propose(data);assert.equal(p.action,'follow_up');assert.equal(p.adjustPlan,true);assert.match(p.title,/hinna/);assert.match(p.why,/plan v2/);assert.match(p.note,/Uppresning/);
});
test('symptoms and unresolved equipment reports take precedence over a time barrier',()=>{
 const symptom=propose({...data,cases:[...data.cases,{code:'changed_symptoms',status:'open'}]});assert.match(symptom.title,/förändrade/);
 const equipment=propose({...data,cases:[...data.cases,{code:'changed_environment',status:'open'}]});assert.match(equipment.title,/förändrats/);
});
