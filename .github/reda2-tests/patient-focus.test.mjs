import test from 'node:test';
import assert from 'node:assert/strict';
import {durationHint,planChanges,changesHTML,contactHint} from '../../reda-2/patient-focus.mjs';
test('timing uses explicit prescription including both sides and never invents missing tempo',()=>{
 assert.equal(durationHint([{side:'both',dose:{sets:2,reps:10,tempo:3,hold:0,rest:30}}]),'Cirka 4 min + egna pauser');
 assert.equal(durationHint([{dose:{sets:2,reps:10}}]),'I din takt');
 assert.equal(durationHint([{dose:{sets:2,reps:10,tempo:-3}}]),'I din takt');
});
test('changes require a known previous version and escape saved text',()=>{
 const a={id:'a',payload:{exercises:[{id:'x',name:'Test',dose:{sets:1,reps:5}}]}},b={id:'b',payload:{exercises:[{id:'x',name:'<img src=x>',dose:{sets:1,reps:8}}]}};
 assert.deepEqual(planChanges(null,b),[]);assert.deepEqual(planChanges(a,a),[]);
 const changes=planChanges(a,b);assert.match(changes[0],/5 repetitioner → 1 omgångar × 8/);assert.ok(!changesHTML(changes,2).includes('<img'));
});
test('contact status never equates a failed read with handled help or unread messages',()=>{
 assert.equal(contactHint({status:'error'},null).title,'Kontaktstatus kunde inte hämtas');
 assert.equal(contactHint({status:'ready',data:{phase:'needs_review'}},null).title,'Din återkoppling finns hos kliniken');
 assert.equal(contactHint(null,{status:'ready',data:{reply_to:'x'}}).kind,'messages');
 assert.equal(contactHint(null,{status:'ready',data:{messages:[]}}),null);
});
