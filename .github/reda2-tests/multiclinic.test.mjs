import test from 'node:test';import assert from 'node:assert/strict';import {unitScope,unitAccess} from '../../reda-2/multiclinic-model.mjs';
test('organization admins can operate across units',()=>assert.equal(unitAccess({role:'admin',status:'active'},null),'organization'));
test('ordinary members require active unit membership',()=>{assert.equal(unitAccess({role:'member',status:'active'},{role:'clinician',status:'active'}),'clinician');assert.equal(unitAccess({role:'member',status:'active'},null),'none')});
test('unit scope falls back safely to organization when selected unit is unavailable',()=>{const s=unitScope({organization:{name:'Klinikgruppen'},units:[{id:'a',name:'City',status:'active'}],selectedUnit:'x'});assert.equal(s.label,'Klinikgruppen');assert.equal(s.isAll,true)});
