const test=require('node:test'),assert=require('node:assert/strict');
const I=require('../../reda-2/intelligence-system.js'),R=require('../../reda-2/training-response.js');
const answers={nextDay:'settled',function:'stable',recovery:'ready',otherTraining:'usual',quality:'controlled',contact:'no'};
test('saved context and instruction stay unchanged across ages and presentation',()=>{
 const plan={goal:'Gå till affären',age:80,context:{stage:'protected',capacity:'high',trainingHistory:'rehab_experienced',goalProfile:'daily',floorOK:false},exercises:[{id:'leg_press',name:'Benpress',instructions:['Min sparade instruktion'],prescribedLoad:'Individuellt vald vikt',dose:{rest:90}}]};
 const before=JSON.stringify(plan),o=I.overview(plan);assert.match(o.focus,/toleransen/);assert.equal(o.constraints.length,1);assert.deepEqual(I.exercise(plan,plan.exercises[0]).steps,['Min sparade instruktion']);assert.equal(I.exercise(plan,plan.exercises[0]).rest,90);assert.deepEqual(I.overview({...plan,age:25,presentation:'trained'}),o);assert.equal(JSON.stringify(plan),before);
});
test('library weight examples are never mistaken for an individual load',()=>{
 const p={exercises:[{id:'leg_press',name:'Benpress',instructions:['Tryck'],prescription:{load:'Exempel: yttre vikt'}}]};assert.equal(I.checks(p)[0].code,'load');p.exercises[0].prescribedLoad='Angiven individuell vikt';assert.deepEqual(I.checks(p),[]);
});
test('all answers must be explicit; unknown is distinct from a normal report',()=>{
 assert.deepEqual(R.normalize(answers),answers);for(const x of [null,[],{}, {...answers,contact:undefined},{...answers,freeText:'oops'},{...answers,nextDay:1}])assert.throws(()=>R.normalize(x));assert.equal(R.signal({...answers,quality:'unknown'}).kind,'incomplete');assert.equal(R.signal(answers).kind,'reported');assert.match(R.signal(answers).detail,/inte ett klartecken/);
});
test('next-day eligibility follows Stockholm dates through DST and excludes open, old and answered sessions',()=>{
 const now='2026-10-26T00:10:00+01:00';
 const s=(id,date,status='completed')=>({id,status,completed_at:date});
 const rows=[s('yesterday','2026-10-25T23:55:00+01:00'),s('same','2026-10-26T00:01:00+01:00'),s('open',null,'partial'),s('rest','2026-10-25T12:00:00Z','planned_rest'),s('old','2026-10-11T12:00:00Z'),s('answered','2026-10-25T14:00:00Z'),s('edge','2026-10-12T12:00:00Z','partial')];
 assert.deepEqual(R.due(rows,[{session_id:'answered'}],now).map(x=>x.id),['yesterday','edge']);assert.deepEqual(R.due([s('bad','not-a-date')],[],now),[]);
});
test('clinical priority is scoped to the selected plan and does not conceal missing data',()=>{
 const rows=[{id:'old',plan_id:'v1',answers:{...answers,nextDay:'worse'}},{id:'ok',plan_id:'v2',answers,created_at:'2026-09-10'},{id:'help',plan_id:'v2',answers:{...answers,quality:'difficult'},created_at:'2026-09-09'}];
 assert.deepEqual(R.summary('v2',rows).rows.map(x=>x.id),['help','ok']);assert.equal(R.summary('v2',rows).attention,1);assert.equal(R.signal({...answers,nextDay:'worse',contact:'yes'}).kind,'review');assert.equal(R.signal({...answers,recovery:'low'}).kind,'load');assert.match(R.clinicalHTML('v2',[],'failure',String),/kunde inte hämtas/);assert.equal(R.summary('v2',[{plan_id:'v2',answers:{}}]).rows[0].signal.kind,'incomplete');
});
