import test from 'node:test';import assert from 'node:assert/strict';import {authoringFocus} from '../../reda-2/authoring-focus-model.mjs';
test('empty plan points to building',()=>assert.equal(authoringFocus({exercises:[],warnings:[]}).phase,'build'));
test('candidate takes precedence because nothing is applied yet',()=>assert.equal(authoringFocus({exercises:[{}],warnings:[]},{candidate:true}).phase,'choose'));
test('warnings block the review-ready state',()=>assert.equal(authoringFocus({exercises:[{}],warnings:['x']}).phase,'fix'));
test('complete plan points to finetune and review',()=>assert.equal(authoringFocus({exercises:[{},{}],warnings:[]}).phase,'review'));
