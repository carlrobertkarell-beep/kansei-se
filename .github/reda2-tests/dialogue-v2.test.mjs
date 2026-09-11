import test from 'node:test';import assert from 'node:assert/strict';import {ask,answer,validateOutput,requestBody,conversationContext} from '../../reda-2/engine/dialogue.mjs';import {fixtures,plan,modelCandidate} from '../../reda-2/evals/dialogue-fixtures.mjs';
import {score} from '../../reda-2/evals/score-dialogue.mjs';
test('report schema excludes the mismatched categories observed in a live response',()=>{
 const choices=requestBody(modelCandidate,'Jag har fått ont i knät',plan).text.format.schema.properties.reports.items.anyOf;
 const permits=(field,value)=>choices.some(c=>c.properties.field.enum.includes(field)&&c.properties.value.enum.includes(value));
 assert.equal(permits('otherTraining','no'),false);
 assert.equal(permits('quality','worse'),false);
 assert.equal(permits('otherTraining','high'),true);
 assert.equal(permits('quality','difficult'),true);
 assert.equal(permits('recovery','unknown'),true);
 assert.throws(()=>validateOutput({intent:'contact',exerciseIndex:0,reports:[{field:'quality',value:'worse',quote:'ont i knät'}]},'Jag har fått ont i knät',plan));
});
test('live evaluator rejects the observed side-routing error and a missing saved-side answer',()=>{
 const f=fixtures.find(x=>x.id==='side');
 const correct={available:true,...answer(f.expected,plan)};
 assert.equal(score(f,correct).pass,true);
 assert.equal(score(f,{available:true,...answer({...f.expected,intent:'execution'},plan)}).pass,false);
 assert.equal(score(f,{...correct,paragraphs:[]}).checks.savedSide,false);
 assert.equal(score(f,{...correct,available:false}).pass,false);
});
for(const f of fixtures)test('fictional routing contract (not live model quality): '+f.id,()=>{const before=JSON.stringify(plan),b=requestBody(modelCandidate,f.question,plan,f.conversation),raw=validateOutput(structuredClone(f.expected),f.question,plan),a=answer(raw,plan);assert.equal(a.canChangePrescription,false);assert.equal(JSON.stringify(plan),before);assert.equal(b.store,false);if(f.expected.intent==='contact')assert.equal(a.contact,true);if(f.expected.intent==='equipment')assert.equal(a.responsePrompt,true)});
test('reports about worsening override erroneous purpose and easy classifications',()=>{for(const intent of ['purpose','too_easy','report']){const a=answer({intent,exerciseIndex:0,reports:[{field:'nextDay',value:'worse',quote:'mer ont'}]},plan);assert.equal(a.intent,'contact');assert.equal(a.contact,true);assert.deepEqual(a.reports,[])}});
test('follow-up context uses bounded user questions and an actual saved exercise',async()=>{let request;const a=await ask({question:'Förklara den enklare',plan,conversation:{exerciseIndex:1,previousQuestions:['Hur gör jag benpress?']},model:modelCandidate,apiKey:'fictional',fetcher:async(u,opts)=>{request=JSON.parse(opts.body);return {ok:true,json:async()=>({status:'completed',output:[{type:'message',content:[{type:'output_text',text:JSON.stringify({intent:'clarify',exerciseIndex:null,reports:[]})}]}]})}}});assert.equal(a.exerciseName,'Benpress');assert.equal(a.stepByStep,true);assert.deepEqual(a.steps,plan.exercises[1].instructions);assert.equal(JSON.parse(request.input[1].content).conversation.previousQuestions.length,1);assert.throws(()=>conversationContext({exerciseIndex:99},plan));assert.throws(()=>conversationContext({previousQuestions:['one','two','three']},plan));assert.throws(()=>conversationContext({previousQuestions:['mail@example.com']},plan))});
test('historical statements cannot be quoted as newly submitted evidence',()=>{assert.throws(()=>validateOutput({intent:'report',exerciseIndex:null,reports:[{field:'nextDay',value:'worse',quote:'mer ont igår'}]},'Varför den övningen?',plan))});
test('missing equipment and ROM use saved values, never invented substitutions',()=>{const a=answer({intent:'equipment',exerciseIndex:1,reports:[]},plan);assert.ok(a.paragraphs.join(' ').includes('Benpressmaskin'));const b=answer({intent:'dose',exerciseIndex:0,reports:[]},plan);assert.ok(b.paragraphs.includes('Ordinerat rörelseomfång: Individuellt angivet rörelseomfång'))});
