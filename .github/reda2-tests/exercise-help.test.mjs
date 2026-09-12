import test from 'node:test';
import assert from 'node:assert/strict';
import {helpAnswer,exerciseSide,helpSummary} from '../../reda-2/exercise-help-model.mjs';
const exercise={id:'extension',name:'Benspark',side:'both',instructions:['Sitt på stolen.','Sträck enligt din instruktion.'],support:'Stol med ryggstöd',equipment:'Ingen extra utrustning',prescribedRange:'Endast inom behandlarens angivna område',prescribedLoad:'Det röda bandet',prescription:{rom:'Bibliotekets exempel',tempo:'Lugn återgång'},dose:{sets:2,reps:6,hold:3,rest:45,tempo:5,label:'2 × 6 per sida'}};
test('help uses the actual saved prescription without translating free text into a new limit',()=>{
 const x=structuredClone(exercise),before=JSON.stringify(x),range=helpAnswer(x,'range');
 assert.equal(range.paragraphs[0],x.prescribedRange);assert.equal(range.frame,null);
 assert.ok(!range.paragraphs.includes(x.prescription.rom));
 const dose=helpAnswer(x,'dose').paragraphs.join(' ');for(const v of ['2 × 6','3 sekunder','45 sekunder','Det röda bandet','Lugn återgång'])assert.ok(dose.includes(v));
 assert.equal(JSON.stringify(x),before);
});
test('missing instructions, side and range remain missing and have a clear next action',()=>{
 for(const t of ['execution','side','range','dose'])assert.equal(helpAnswer({},t).missing,true,t);
 assert.equal(helpAnswer({},'setup').frame,0);assert.equal(helpAnswer(exercise,'diagnose'),null);
});
test('the current round determines the visible side without replacing the prescribed bilateral schedule',()=>{
 assert.equal(exerciseSide(exercise,{side:'left'}),'left');assert.equal(exerciseSide(exercise,{side:'right'}),'right');assert.equal(exercise.side,'both');
 assert.equal(exerciseSide({...exercise,side:'right'},{side:'left'}),'right');assert.equal(exerciseSide({}),null);
});
test('explanations preserve clinician instructions and support instead of filling with generic text',()=>{
 assert.deepEqual(helpAnswer(exercise,'execution').paragraphs,exercise.instructions);
 assert.deepEqual(helpAnswer(exercise,'setup').paragraphs,[exercise.support,exercise.equipment,exercise.instructions[0]]);
});
test('clinical summary distinguishes perceived understanding from a completed clinical review',()=>{
 const h={exercise_name:'Benspark',exercise:{side:'right'},plan_version:3,option_label:'Kortare pass',topics:['side','range'],outcome:'needs_help',note:'Jag förstår inte vinkeln'};
 const summary=helpSummary(h).join(' ');for(const v of ['Höger sida','plan v3','Kortare pass','Vilken sida?','Hur långt?','fortfarande hjälp','Jag förstår inte vinkeln'])assert.ok(summary.includes(v));
 assert.match(helpSummary({...h,outcome:'clear'})[2],/Patienten uppger/);
});
