import test from 'node:test';import assert from 'node:assert/strict';
import {basisReadiness,goalChange,basisHTML} from '../../reda-2/patient-basis.mjs';
import {propose} from '../../reda-2/engine/clinic-proposals.mjs';
test('missing data and conflicting goals are explicit',()=>{const gaps=basisReadiness({profile:{goal:'A'},plan:{goal:'B'}},'2026-09-12');assert.ok(gaps.some(x=>x.label.includes('skiljer')));assert.ok(gaps.some(x=>x.target==='report'));assert.ok(gaps.some(x=>x.label.includes('Behandlingsfokus')))});
test('old patient circumstances require reconfirmation',()=>{assert.ok(basisReadiness({profile:{focus:'Knä'},plan:{goal:'Gå'},latest:{created_at:'2026-07-01'}},'2026-09-12').some(x=>x.label.includes('30 dagar')))});
test('goal comparison cannot mix different goals',()=>{assert.equal(goalChange({latest:{goal_key:'b',answers:{ability:8}},baseline:{goal_key:'a',answers:{ability:3}}}),null);assert.equal(goalChange({latest:{goal_key:'a',answers:{ability:8}},baseline:{goal_key:'a',answers:{ability:3}}}),5)});
test('source labels escape patient input',()=>{const h=basisHTML({profile:{focus:'<img>'}},'2026-09-12');assert.ok(h.includes('&lt;img&gt;'));assert.ok(!h.includes('<img>'))});
test('new goal report yields review, never automatic clinical change',()=>{const p=propose({today:'2026-09-12',patient:{},cases:[{status:'open',checkin:{answers:{ability:3,minutes:10}}}]});assert.equal(p.action,'follow_up');assert.ok(p.why.includes('3/10'));assert.ok(p.note.includes('innan en klinisk ändring'))});
