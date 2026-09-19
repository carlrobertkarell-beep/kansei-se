// Trusted service worker only. Claims durable EI jobs and invokes the same database-owned progression engine.
const batch=Number(Deno.env.get('REDA_EI_BATCH')||25);
const url=Deno.env.get('SUPABASE_URL'),key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
if(!url||!key)throw Error('EI worker service credentials are missing');
const headers={apikey:key,Authorization:'Bearer '+key,'Content-Type':'application/json'};
async function rpc(name,body){const r=await fetch(url+'/rest/v1/rpc/'+name,{method:'POST',headers,body:JSON.stringify(body)});if(!r.ok)throw Error(name+' '+r.status+' '+await r.text());const t=await r.text();return t?JSON.parse(t):null}
Deno.serve(async()=>{let jobs=[];try{jobs=await rpc('reda_worker_claim',{p_limit:batch})||[]}catch(e){return new Response(String(e),{status:500})}
 let done=0,failed=0;for(const job of jobs){try{await rpc('reda_worker_evaluate',{p_queue_id:job.id,p_patient_id:job.patient_id});done++}catch(e){failed++;try{await rpc('reda_worker_fail',{p_queue_id:job.id,p_error:String(e)})}catch{}}}
 return Response.json({claimed:jobs.length,done,failed})});
