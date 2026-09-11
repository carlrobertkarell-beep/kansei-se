import { createClient } from 'npm:@supabase/supabase-js@2.116.0'
import { ask,validateQuestion } from '../../../engine/dialogue.mjs'
const origins=new Set(['https://www.kansei.se','https://kansei.se']);
const headers=(req:Request)=>({'Content-Type':'application/json','Access-Control-Allow-Origin':origins.has(req.headers.get('origin')||'')?req.headers.get('origin')!:'https://www.kansei.se','Access-Control-Allow-Headers':'authorization, apikey, content-type, x-client-info','Access-Control-Allow-Methods':'POST, OPTIONS','Vary':'Origin'});
Deno.serve(async(req:Request)=>{
 const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:headers(req)});
 if(req.headers.get('origin')&&!origins.has(req.headers.get('origin')!))return json({error:'Origin not allowed'},403);
 if(req.method==='OPTIONS')return new Response('ok',{headers:headers(req)});if(req.method!=='POST')return json({error:'Method not allowed'},405);
 if(Number(req.headers.get('content-length')||0)>14000)return json({error:'Frågan är för lång.'},413);
 const token=req.headers.get('authorization');if(!token?.startsWith('Bearer '))return json({error:'Logga in igen.'},401);
 try{
  const text=await req.text();if(text.length>14000)return json({error:'Frågan är för lång.'},413);const body=JSON.parse(text);
  if(!/^[0-9a-f-]{36}$/i.test(body.plan_id||'')||!['capabilities','ask'].includes(body.action))return json({error:'Ogiltig förfrågan.'},400);
  if(body.action==='ask')validateQuestion(body.question);
  const db=createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_ANON_KEY')!,{global:{headers:{Authorization:token}},auth:{persistSession:false,autoRefreshToken:false}});
  const {data,error}=await db.rpc('reda_dialogue_context',{p_plan_id:body.plan_id,p_consume:body.action==='ask'});
  if(error)return json({error:error.code==='42501'?'Logga in igen eller öppna din aktuella plan.':'AI-stödet kan inte startas just nu. Försök senare.'},error.code==='42501'?403:429);
  const apiKey=Deno.env.get('OPENAI_API_KEY'),model=Deno.env.get('OPENAI_REDA_MODEL'),configured=!!apiKey&&!!model;
  if(body.action==='capabilities'||!data.enabled||!configured)return json({available:data.enabled&&configured,reason:data.enabled&&configured?null:'not_enabled'});
  const result=await ask({question:body.question,plan:data.plan,conversation:body.conversation||{},model,apiKey,endpoint:Deno.env.get('OPENAI_REDA_ENDPOINT')||'https://api.openai.com/v1/responses'});
  return json(result);
 }catch(e){return json({error:e instanceof Error?e.message:'Frågan kunde inte behandlas.'},400)}
});
