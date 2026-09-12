import { withSupabase } from 'npm:@supabase/server@1.5.3'
import { createClient } from 'npm:@supabase/supabase-js@2.116.0'
import { corsHeaders } from 'jsr:@supabase/supabase-js@2.116.0/cors'
const headers={...corsHeaders,'access-control-allow-headers':(corsHeaders['access-control-allow-headers']||'authorization, x-client-info, apikey, content-type')+', x-reda-organization'}
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{...headers,'Content-Type':'application/json'}})
const handler=withSupabase({auth:'user'},async(req,_ctx)=>{
 if(req.method!=='POST')return json({error:'Method not allowed'},405);
 const body=await req.json().catch(()=>null);
 if(!body?.handover_id||!body?.organization_id)return json({error:'Välj en granskad överlämning.'},400);
 const url=Deno.env.get('SUPABASE_URL')!,key=Deno.env.get('SUPABASE_ANON_KEY')!;
 const scoped=createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false},global:{headers:{Authorization:req.headers.get('Authorization')||'','x-reda-organization':body.organization_id}}});
 const {data:attempt,error}=await scoped.rpc('reda_reserve_invitation',{p_handover_id:body.handover_id});
 if(error)return json({error:error.message},error.code==='54000'?429:403);
 if(attempt.accepted)return json({accepted:true});
 const admin=createClient(url,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false,autoRefreshToken:false}});
 let accepted=false;
 try{
  const redirectTo='https://www.kansei.se/reda-2/patient.html';
  const {error:inviteError}=await admin.auth.admin.inviteUserByEmail(attempt.email,{redirectTo});
  if(!inviteError)accepted=true;
  else if(['email_exists','user_already_exists'].includes(inviteError.code||'')){
   const sender=createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}});
   const {error:otpError}=await sender.auth.signInWithOtp({email:attempt.email,options:{shouldCreateUser:false,emailRedirectTo:redirectTo}});accepted=!otpError;
  }
 }catch{accepted=false}
 const {error:receiptError}=await admin.rpc('reda_finish_invitation',{p_id:attempt.id,p_lease:attempt.lease,p_accepted:accepted});
 if(receiptError)return json({error:'Utskickets kvitto kunde inte sparas. Vänta en minut innan du kontrollerar igen.'},503);
 return accepted?json({accepted:true}):json({error:'Planen är publicerad, men e-posttjänsten kunde inte bekräfta utskicket. Kontrollera e-postinställningar och försök igen.'},502)
})
export default{fetch:(req:Request)=>req.method==='OPTIONS'?new Response('ok',{headers}):handler(req)}
