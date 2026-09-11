/* Explicit opt-in, fictional data only. No Supabase access or production feature changes. */
import {ask,requestBody} from '../engine/dialogue.mjs';
import {fixtures,plan,modelCandidate} from './dialogue-fixtures.mjs';
import {score} from './score-dialogue.mjs';
if(!process.argv.includes('--live-fixtures')){
 for(const f of fixtures)requestBody(modelCandidate,f.question,plan,f.conversation);
 console.log(JSON.stringify({mode:'dry-run',cases:fixtures.length,modelCandidate,externalCalls:0,measuredModelQuality:false}));
}else{
 if(!process.env.OPENAI_API_KEY)throw Error('OPENAI_API_KEY is required for explicit fictional evaluation. No call made.');
 const results=[];
 for(const f of fixtures){
  const start=Date.now();
  try{
   const a=await ask({question:f.question,plan,conversation:f.conversation,model:modelCandidate,apiKey:process.env.OPENAI_API_KEY,endpoint:process.env.OPENAI_REDA_ENDPOINT||'https://api.openai.com/v1/responses'});
   results.push({id:f.id,...score(f,a),intent:a.intent,latencyMs:Date.now()-start,usage:a.usage});
  }catch{results.push({id:f.id,pass:false,error:'request_or_validation_failed',latencyMs:Date.now()-start})}
 }
 console.log(JSON.stringify({mode:'live-fictional',model:modelCandidate,results},null,2));if(results.some(x=>!x.pass))process.exitCode=1;
}
