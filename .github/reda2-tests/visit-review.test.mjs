import test from 'node:test';import assert from 'node:assert/strict';import {normalizeVisitReview,visitHandoff} from '../../reda-2/visit-review-model.mjs';
test('visit review requires explicit clinician outcome and note',()=>{assert.throws(()=>normalizeVisitReview({outcome:'keep',note:'ok'}));assert.equal(normalizeVisitReview({outcome:'adjust',note:'Fortsatt belastningsbedömning.'}).outcome,'adjust')});
test('keep does not open authoring while adjust and new do',()=>{assert.equal(visitHandoff('keep').openPlan,false);assert.equal(visitHandoff('adjust').mode,'manual');assert.equal(visitHandoff('new').mode,'suggest')});
test('unknown outcome fails closed',()=>assert.equal(visitHandoff('progress'),null));
