import { withSupabase } from 'npm:@supabase/server@1.5.3'
import { corsHeaders } from 'jsr:@supabase/supabase-js@2.116.0/cors'
const headers={...corsHeaders,'access-control-allow-headers':(corsHeaders['access-control-allow-headers']||'authorization, x-client-info, apikey, content-type')+', x-reda-organization'}
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{...headers,'Content-Type':'application/json'}})
const handler=withSupabase({auth:'user'},async(req,_ctx)=>{
 if(req.method!=='POST')return json({error:'Method not allowed'},405);
 return json({error:'Patientaktivering och inbjudningar är inte öppnade.'},403)
})
export default{fetch:(req:Request)=>req.method==='OPTIONS'?new Response('ok',{headers}):handler(req)}
