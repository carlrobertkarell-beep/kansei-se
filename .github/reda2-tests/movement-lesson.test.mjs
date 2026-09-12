import test from 'node:test';
import assert from 'node:assert/strict';
import {lessonInstructions,lessonSegments,wholeLessonSequence,focusCamera,createLessonPlayback,localSwedishVoice} from '../../reda-2/movement-lesson-model.mjs';
function harness(){let now=0,callback=null,draws=[],changes=[];const player=createLessonPlayback({draw:x=>draws.push(x),change:x=>changes.push(x),clock:()=>now,request:cb=>{callback=cb;return 1},cancel:()=>{callback=null}});return {player,draws,changes,advance(ms){now+=ms;const cb=callback;callback=null;cb?.(now)},scheduled:()=>!!callback}}
test('a teaching segment stops at its endpoint and never loops or advances another part',()=>{const h=harness();h.player.select({from:.23,to:1,seconds:10});h.player.play();h.advance(11000);assert.equal(h.player.state().position,1);assert.equal(h.player.state().playing,false);assert.equal(h.scheduled(),false);h.advance(200000);assert.equal(h.player.state().position,1)});
test('pause and speed changes preserve the exact current position; resume excludes paused time',()=>{const h=harness();h.player.select({from:0,to:1,seconds:10});h.player.play();h.advance(3000);h.player.pause();const at=h.player.state().position;h.advance(60000);assert.equal(h.player.state().position,at);h.player.play();assert.equal(h.player.state().position,at);h.player.speed(true);assert.equal(h.player.state().position,at);h.advance(1500);assert.ok(Math.abs(h.player.state().progress-.4)<1e-8)});
test('choosing a part paints its starting point and waits for an explicit play',()=>{const h=harness();h.player.select({from:1,to:0,seconds:12});assert.equal(h.player.state().position,1);assert.equal(h.scheduled(),false);h.advance(100000);assert.equal(h.player.state().position,1);h.player.play();h.advance(12000);assert.equal(h.player.state().position,0);h.player.play();assert.equal(h.player.state().position,1)});
test('chair learning has a separate forward lean and longer return; other families can use the same player',()=>{const s=lessonSegments('sit-to-stand.support');assert.equal(s.length,3);assert.equal(s[0].to,s[1].from);assert.equal(s[1].to,s[2].from);assert.equal(s[2].to,0);assert.ok(s[2].seconds>=s[1].seconds);assert.equal(lessonSegments('knee-extension.seated').length,2)});
test('learning uses the saved instruction verbatim, deduplicates it and does not invent missing content',()=>{const x={support:'Mitt handstöd',instructions:['  Min individuella instruktion. ','Min individuella instruktion.','Nästa sak.'],prescribedRange:'Min gräns',dose:{sets:3,reps:8}};const before=structuredClone(x);assert.deepEqual(lessonInstructions(x),['Utrustning och stöd: Mitt handstöd','Min individuella instruktion.','Nästa sak.','Ditt rörelseomfång: Min gräns']);assert.deepEqual(x,before);assert.deepEqual(lessonInstructions({}),[]);assert.deepEqual(lessonInstructions({instruction:'Den enda instruktionen.'}),['Den enda instruktionen.'])});
test('patient instructions can only be read with an explicitly local Swedish voice',()=>{const remote={lang:'sv-SE',localService:false},unknown={lang:'sv-SE'},local={lang:'sv-SE',localService:true};assert.equal(localSwedishVoice([remote,unknown]),null);assert.equal(localSwedishVoice([{lang:'en-US',localService:true},remote,local]),local)});

test('a whole demonstration crosses each part, returns to start and stops after one cycle',()=>{
 for(const [key,peak] of [['sit-to-stand.support',8300],['knee-extension.seated',7000]]){
  const h=harness(),s=wholeLessonSequence(key);h.player.select(s);h.player.play();h.advance(500);assert.equal(h.player.state().position,0);
  h.advance(4000);assert.ok(h.player.state().position>0&&h.player.state().position<1);
  h.advance(peak-4500);assert.equal(h.player.state().position,1);
  h.advance(11000-peak);assert.ok(h.player.state().position>0&&h.player.state().position<1);
  h.advance(3001);assert.equal(h.player.state().position,0);assert.equal(h.player.state().complete,true);assert.equal(h.scheduled(),false);
  h.advance(100000);assert.equal(h.player.state().position,0);
 }
});
test('whole demonstration pause and slow speed preserve progress through the return',()=>{
 const h=harness();h.player.select(wholeLessonSequence('sit-to-stand.support'));h.player.play();h.advance(10000);h.player.pause();const at=h.player.state().position;h.advance(60000);h.player.speed(true);assert.equal(h.player.state().position,at);h.player.play();h.advance(1500);assert.ok(h.player.state().position<at);h.advance(4500);assert.equal(h.player.state().complete,true);assert.equal(h.player.state().playing,false)
});

test('paused close view includes the far side and all body landmarks without mutating the pose',()=>{
 const pose={head:[240,110],shoulder:[240,150],hip:[220,230],knee:[290,245],ankle:[300,330],toe:[325,350],back:{heel:[185,360]}};const before=structuredClone(pose),[x,y,w,h]=focusCamera(pose);assert.ok(x<185&&x+w>325&&y<110&&y+h>360);assert.deepEqual(pose,before);assert.equal(focusCamera({head:[NaN,2]}),null)
});
