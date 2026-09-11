import { withSupabase } from 'npm:@supabase/server@1.5.3'
import { corsHeaders } from 'jsr:@supabase/supabase-js@2.116.0/cors'
const headers={...corsHeaders,'access-control-allow-headers':(corsHeaders['access-control-allow-headers']||'authorization, x-client-info, apikey, content-type')+', x-reda-organization'}
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{...headers,'Content-Type':'application/json'}})
// Existing memberships are the authority. Signing in never restores a revoked role.
const handler=withSupabase({auth:'user'},async(req,ctx)=>{
 if(req.method!=='POST')return json({error:'Method not allowed'},405);
 const {data,error}=await ctx.supabase.rpc('reda_my_workspaces');
 if(error||!Array.isArray(data)||!data.length)return json({error:'Kontot saknar en aktiv arbetsyta.'},403);
 return json({ok:true})
})
export default{fetch:(req:Request)=>req.method==='OPTIONS'?new Response('ok',{headers}):handler(req)}
