import test from 'node:test';import assert from 'node:assert/strict';import {prepareCorridor,corridorDiff} from '../../reda-2/progression-corridor.mjs';
const plan={payload:{exercises:[{id:'e',name:'Benspark',side:'both',variantId:'seated',dose:{sets:2,reps:8}}]}};
test('corridor starts with exact current prescription and deterministic dose steps',()=>{const c=prepareCorridor(plan);assert.equal(c.steps[0].prescription[0].dose.reps,8);assert.equal(c.steps[1].prescription[0].dose.reps,9);assert.equal(c.steps[2].prescription[0].dose.sets,3);assert.equal(c.steps[3].prescription[0].dose.reps,10)});
test('corridor never mutates current plan',()=>{const before=JSON.stringify(plan);prepareCorridor(plan);assert.equal(JSON.stringify(plan),before)});
test('diff exposes only changed prescriptions',()=>assert.equal(corridorDiff(plan.payload.exercises,prepareCorridor(plan).steps[1].prescription).length,1));
test('missing prescription fails closed',()=>assert.equal(prepareCorridor({payload:{exercises:[]}}).valid,false));
