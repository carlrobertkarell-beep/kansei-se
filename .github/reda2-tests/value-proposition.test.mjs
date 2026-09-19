import test from 'node:test';import assert from 'node:assert/strict';import {valuePillars} from '../../reda-2/value-proposition.mjs';
test('clinic value is operational rather than generic exercise-app copy',()=>{const x=valuePillars('clinic');assert.ok(x.some(v=>/undantag/i.test(v.title)));assert.ok(x.some(v=>/mellan besöken/i.test(v.title)))});
test('consumer value includes transparency and human handoff',()=>{const x=valuePillars('consumer');assert.ok(x.some(v=>/ändrats/i.test(v.title)));assert.ok(x.some(v=>/människa/i.test(v.title)))});
