import test from 'node:test';import assert from 'node:assert/strict';
import {clinicWorkflow,patientSupportText} from '../../reda-2/support-workflow.mjs';
import {propose} from '../../reda-2/engine/clinic-proposals.mjs';
test('sent question retains open followup rather than claiming resolution',()=>{const r=propose({patient:{connected:true,patient_status:'active',followup_date:'2026-09-20'},today:'2026-09-12',cases:[],workflow:{phase:'awaiting_patient'}});assert.equal(r.action,'follow_up');assert.equal(r.due,'2026-09-20');assert.match(r.effect,/förblir öppet/)});
test('completed contact requires explicit resolution',()=>{const r=propose({patient:{},today:'2026-09-12',cases:[],workflow:{phase:'needs_resolution'}});assert.equal(r.action,'resolve_cases');assert.equal(r.note,'')});
test('patient handling receipt never claims recovery or booking',()=>{assert.match(patientSupportText({phase:'handled'}).detail,/inte att dina besvär/);assert.match(patientSupportText({phase:'scheduled'}).detail,/inte att ett besök är bokat/);assert.equal(patientSupportText({phase:'none'}),null)});
test('clinical status escapes server text and identifies overdue work',()=>{const html=clinicWorkflow({phase:'scheduled',due_date:'<img>',overdue:true});assert.match(html,/Försenad/);assert.ok(!html.includes('<img>'));assert.equal(clinicWorkflow({phase:'none'}),'')});
