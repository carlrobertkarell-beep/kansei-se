import test from 'node:test';
import assert from 'node:assert/strict';
import {previewGroup} from '../../reda-2/shadow-fleet.mjs';
test('only an explicit ready advance goes into the ready group',()=>{
 assert.equal(previewGroup({action:'advance',code:'ready'}),'ready');
 for(const d of [null,{}, {action:'advance',code:'pending_review'},{action:'blocked',code:'ready'},{action:'complete',code:'complete'}])assert.equal(previewGroup(d),'review');
});
test('missing approval stays outside clinical decision groups',()=>{
 assert.equal(previewGroup({action:'none',code:'no_frame'}),'uncovered');
 assert.equal(previewGroup({action:'wait',code:'evidence'}),'waiting');
 assert.equal(previewGroup({action:'hold',code:'load'}),'waiting');
});
