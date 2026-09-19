import test from 'node:test';import assert from 'node:assert/strict';import {graphCorridor,validateGraph} from '../../reda-2/progression-graph.mjs';
const plan={payload:{exercises:[{id:'sit',name:'Uppresning',variantId:'supported',side:'simultaneous',dose:{sets:2,reps:8}}]}};
const bp={progressionGraph:{start:'a',nodes:[{id:'a',label:'Mer volym',exercises:{sit:{dose:{reps:10}}}},{id:'b',label:'Mindre stöd',exercises:{sit:{variantId:'standard'}}}],edges:[{from:'a',to:'b',kind:'advance'}]}};
test('blueprint graph produces reviewed prescription nodes',()=>{const c=graphCorridor(plan,bp);assert.equal(c.source,'blueprint');assert.equal(c.steps[1].prescription[0].dose.reps,10);assert.equal(c.steps[2].prescription[0].variantId,'standard')});
test('graph validation rejects dangling edges',()=>{assert.equal(validateGraph(bp.progressionGraph),true);assert.equal(validateGraph({nodes:[{id:'a'}],edges:[{from:'a',to:'x'}]}),false)});
test('absence of graph falls back to conservative dose corridor',()=>assert.equal(graphCorridor(plan,{}).source,'dose'));
