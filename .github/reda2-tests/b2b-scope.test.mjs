import test from 'node:test';import assert from 'node:assert/strict';import {b2bScopeOptions,b2bBreadcrumb} from '../../reda-2/b2b-scope-model.mjs';
test('organization scope is always first and units follow',()=>{const x=b2bScopeOptions({name:'Gruppen'},[{id:'b',name:'City',status:'active'},{id:'x',name:'Stängd',status:'disabled'}]);assert.deepEqual(x.map(v=>v.label),['Gruppen','City'])});
test('breadcrumb supports organization unit and clinician',()=>assert.equal(b2bBreadcrumb({name:'Gruppen'},{name:'City'},{display_name:'Anna'}),'Gruppen / City / Anna'));
