const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');const c={console,TextEncoder,TextDecoder,crypto:require('crypto').webcrypto};c.window=c;c.globalThis=c;vm.createContext(c);for(const f of ['data.js','clinical-model-v2.js','clinical-addons.js','clinical-library-v3.js','exercise-intelligence-knee.js','exercise-intelligence-next.js','exercise-quality.js','exercise-graph.js','core.js','planner.js','session-state.js'])vm.runInContext(fs.readFileSync('reda-2/'+f,'utf8'),c);const P=c.RedaPlanner,S=c.RedaSession,options={blueprintId:'knee_pf',capacity:'high',stage:'build',trainingHistory:'rehab_experienced',equipment:'gym',goalProfile:'strength',floorOK:true,band:true};
test('clinician dose change keeps original plan immutable',()=>{const p=P.buildProgram(options),q=P.editExercise(p,0,{sets:4,reps:7,prescribedLoad:'12 kg'});assert.equal(q.exercises[0].dose.reps,7);assert.match(q.exercises[0].dose.label,/7/);assert.equal(q.exercises[0].prescribedLoad,'12 kg');assert.notEqual(p.exercises[0].dose.reps,7)});
test('variant change carries new movement and prescription together',()=>{const p=P.buildProgram(options),i=p.exercises.findIndex(x=>x.id==='leg_press');assert.ok(i>=0);const q=P.editExercise(p,i,{variantId:'single'});assert.equal(q.exercises[i].motionKey,'leg-press.single');assert.equal(q.exercises[i].side,'both');assert.match(q.exercises[i].prescription.target,/Unilateral/)});
test('unavailable variant and invalid dose are refused',()=>{const p=P.buildProgram(options);assert.throws(()=>P.editExercise(p,0,{variantId:'invented'}));assert.throws(()=>P.editExercise(p,0,{sets:0}));assert.throws(()=>P.editExercise(p,0,{reps:1.5}))});
test('home restrictions are never silently dropped',()=>{const p=P.buildProgram({...options,equipment:'home',floorOK:false,band:false});for(const x of p.exercises){const e=c.RedaData.exercises.find(e=>e.id===x.id),v=e.variants.find(v=>v.id===x.variantId);assert.ok(!v.tags?.floor&&!v.tags?.band&&!v.tags?.gym)}assert.ok(p.warnings.length>0)});
test('both sides need a separate explicit round each',()=>{const x={id:'extension',side:'both',dose:{sets:2}},s=S.create([x],'test','2026-09-10T12:00:00Z');assert.equal(s.progress[0].totalRounds,4);assert.throws(()=>S.mark(s,0,3));let n=S.mark(s,0,0);assert.equal(n.progress[0].status,'partial');assert.throws(()=>S.mark(n,0,0));for(let i=1;i<4;i++)n=S.mark(n,0,i);assert.equal(n.progress[0].status,'completed');assert.equal(s.progress[0].roundsDone,0)});
test('undo removes exactly the last marked side and clears stale feedback immutably',()=>{
 const initial=S.create([{id:'x',side:'both',dose:{sets:1}}],'t','now');
 const first=S.mark(initial,0,0),done=S.mark(first,0,1);done.progress[0].feedback='heavy';
 const before=JSON.stringify(done),undone=S.undo(done,0);
 assert.equal(JSON.stringify(done),before);assert.equal(undone.progress[0].roundsDone,1);assert.equal(undone.progress[0].status,'partial');assert.equal(undone.progress[0].feedback,null);
 assert.equal(S.rounds({side:'both',dose:{sets:1}})[undone.progress[0].roundsDone].side,'right');
 const pending=S.undo(undone,0);assert.equal(pending.progress[0].roundsDone,0);assert.equal(pending.progress[0].status,'pending');assert.throws(()=>S.undo(pending,0));
 assert.equal(S.mark(undone,0,1).progress[0].status,'completed');assert.equal(initial.progress[0].roundsDone,0);
});
test('skip and resume retain partial rounds and meaningful feedback without mutating inputs',()=>{
 const initial=S.create([{id:'x',dose:{sets:3}},{id:'y',dose:{sets:1}}],'t','now'),partial=S.mark(initial,0,0);partial.progress[0].feedback='heavy';
 const before=JSON.stringify(partial),skipped=S.skip(partial,0);
 assert.equal(JSON.stringify(partial),before);assert.equal(skipped.progress[0].status,'skipped');assert.equal(skipped.progress[0].roundsDone,1);assert.equal(skipped.progress[0].feedback,'heavy');assert.throws(()=>S.mark(skipped,0,1));
 const resumed=S.resume(skipped,0);assert.equal(skipped.progress[0].status,'skipped');assert.equal(resumed.progress[0].status,'partial');assert.equal(resumed.progress[0].roundsDone,1);assert.equal(resumed.progress[0].feedback,'heavy');assert.equal(S.mark(resumed,0,1).progress[0].roundsDone,2);
 assert.equal(resumed.progress[1].status,'pending');assert.notEqual(resumed.progress[1],skipped.progress[1]);assert.throws(()=>S.resume(resumed,0));
});
test('skipping an unstarted exercise clears feedback and resuming restores pending',()=>{
 const initial=S.create([{id:'x',dose:{sets:1}}],'t','now');initial.progress[0].feedback='light';
 const skipped=S.skip(initial,0),resumed=S.resume(skipped,0);
 assert.equal(initial.progress[0].feedback,'light');assert.equal(skipped.progress[0].roundsDone,0);assert.equal(skipped.progress[0].feedback,null);assert.equal(resumed.progress[0].status,'pending');assert.equal(resumed.progress[0].roundsDone,0);
 assert.throws(()=>S.skip(S.mark(resumed,0,0),0));
});
test('finishing early retains completed, partial, pending and skipped progress exactly',()=>{
 let initial=S.create(['completed','partial','pending','skipped'].map(id=>({id,dose:{sets:2}})),'t','now');
 initial=S.mark(S.mark(initial,0,0),0,1);initial=S.mark(initial,1,0);initial=S.skip(initial,3);initial.progress[1].feedback='heavy';
 const before=JSON.stringify(initial),finished=S.finish(initial,'later');
 assert.equal(JSON.stringify(initial),before);assert.equal(finished.status,'partial');assert.equal(finished.completedAt,'later');assert.equal(JSON.stringify(finished.progress),JSON.stringify(initial.progress));assert.notEqual(finished.progress,initial.progress);
});
test('only fully completed exercises produce a completed session',()=>{
 const initial=S.create([{id:'x',dose:{sets:1}}],'t','now'),done=S.mark(initial,0,0),finished=S.finish(done,'later');
 assert.equal(finished.status,'completed');assert.equal(finished.completedAt,'later');assert.equal(done.completedAt,null);assert.equal(done.status,'partial');assert.equal(finished.progress[0].roundsDone,1);
 assert.equal(S.finish(initial,'later').status,'partial');assert.throws(()=>S.finish(initial));
});
test('finished sessions reject every transition without changing stored progress',()=>{
 const initial=S.create([{id:'x',dose:{sets:2}}],'t','now');
 for(const finished of [S.finish(initial,'later'),S.finish(S.skip(S.mark(initial,0,0),0),'later'),S.finish(S.mark(S.mark(initial,0,0),0,1),'later'),{...initial,status:'completed'}]){
  const before=JSON.stringify(finished);
  for(const change of [()=>S.mark(finished,0,0),()=>S.undo(finished,0),()=>S.skip(finished,0),()=>S.resume(finished,0),()=>S.finish(finished,'even later')])assert.throws(change);
  assert.equal(JSON.stringify(finished),before);
 }
});
test('exercise transitions validate indices and preserve the session on refusal',()=>{
 const initial=S.create([{id:'x',dose:{sets:2}}],'t','now'),before=JSON.stringify(initial);
 for(const index of [-1,1,0.5,'0',null,undefined])for(const change of [()=>S.mark(initial,index,0),()=>S.undo(initial,index),()=>S.skip(initial,index),()=>S.resume(initial,index)])assert.throws(change);
 for(const round of [-1,0.5,'0',null,undefined])assert.throws(()=>S.mark(initial,0,round));
 assert.equal(JSON.stringify(initial),before);
});
test('follow-up distinguishes completed, partial and reported problems',()=>{const s=S.summary([{status:'completed',payload:{exercises:[{exerciseId:'x',feedback:'heavy'}]}},{status:'partial',payload:{exercises:[{exerciseId:'x',status:'skipped'}]}}]);assert.equal(s.completed,1);assert.equal(s.partial,1);assert.equal(s.issues.x,2)});

test('step-up never reuses a chair-rise movement',()=>{const p=P.buildProgram({...options,equipment:'home',capacity:'supported',stage:'protected',trainingHistory:'new'});const x=p.exercises.find(x=>x.id==='step_up');assert.equal(x.motionKey,'step-up.supported')});
