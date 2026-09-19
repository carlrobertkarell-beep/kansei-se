import test from 'node:test';
import assert from 'node:assert/strict';
import {shadowReview,renderShadowReview} from '../../reda-2/shadow-review.mjs';
const frame={id:'f1',execution:'shadow',status:'approved',current_step:0,current_plan_id:'p1',policy:{validFrom:'2026-09-01',validUntil:'2026-10-01'}};
const decision=(id,extra={})=>({id,frame_id:'f1',plan_id:'p1',step:0,action:'advance',applied:false,created_at:'2026-09-19T10:00:00Z',...extra});
const build=extra=>shadowReview({frame,activePlanId:'p1',now:new Date('2026-09-19T12:00:00Z'),...extra});
test('only the active shadow frame, plan and level are counted, with deduplication',()=>{
 const s=build({decisions:[decision('a'),decision('a'),decision('b',{frame_id:'old'}),decision('c',{plan_id:'old'}),decision('d',{step:1}),{id:'legacy',action:'advance'}]});
 assert.equal(s.counts.total,1);assert.equal(s.counts.unreviewed,1);assert.equal(s.nextId,'a');
});
test('real persisted verdicts retain disagreements and uncertainty',()=>{
 const s=build({decisions:[decision('a',{review:[{verdict:'agree'}]}),decision('b',{review:{verdict:'disagree'}}),decision('c',{review:{verdict:'uncertain'}}),decision('d',{review:[]})]});
 assert.deepEqual(s.counts,{total:4,agree:1,disagree:1,uncertain:1,unreviewed:1});assert.equal(s.state,'attention');assert.equal(s.nextId,'d');
});
test('reviewing all displayed decisions never enables autonomy',()=>{
 const s=build({decisions:[decision('a',{review:{verdict:'agree'}})]});
 assert.equal(s.state,'reviewed');assert.equal(s.canEnableAutomatic,false);assert.equal(s.nextId,null);assert.match(renderShadowReview(s),/senaste 20 besluten/);
});
test('acknowledged cases, mismatched plan and expired frame remain visible',()=>{
 const s=build({frame:{...frame,policy:{...frame.policy,validUntil:'2026-09-18'}},activePlanId:'p2',cases:[{status:'acknowledged'},{status:'resolved'}]});
 assert.equal(s.state,'attention');assert.equal(s.findings.length,3);assert.equal(s.canEnableAutomatic,false);
});
test('latest hold remains visible even when a clinician agrees with it',()=>{
 const s=build({decisions:[decision('a',{review:{verdict:'agree'},created_at:'2026-09-18'}),decision('b',{action:'hold',review:{verdict:'agree'}})]});
 assert.equal(s.state,'attention');assert.match(s.findings.join(' '),/avvakta/);
});
test('empty history is not evidence of readiness; automatic and revoked frames are excluded',()=>{
 assert.equal(build().state,'empty');assert.equal(build().canEnableAutomatic,false);
 assert.equal(build({frame:{...frame,execution:'automatic'}}),null);assert.equal(build({frame:{...frame,status:'revoked'}}),null);
});
