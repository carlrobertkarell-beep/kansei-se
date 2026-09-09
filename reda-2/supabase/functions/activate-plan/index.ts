import { withSupabase } from 'npm:@supabase/server@1.5.3'

export default {
  fetch: withSupabase({ auth: 'user' }, async (req, ctx) => {
    if (req.method !== 'POST') return Response.json({error:'Method not allowed'},{status:405})
    if (ctx.jwtClaims?.aal !== 'aal2') return Response.json({error:'MFA required'},{status:403})
    const actorId=ctx.userClaims?.id
    if(!actorId) return Response.json({error:'Sign in required'},{status:401})
    const {data:profile,error:profileError}=await ctx.supabase.from('reda_profiles').select('role').eq('user_id',actorId).single()
    if(profileError||profile?.role!=='clinician') return Response.json({error:'Clinician required'},{status:403})
    const body=await req.json().catch(()=>null); const planId=body?.plan_id
    if(!planId) return Response.json({error:'Invalid request'},{status:400})
    const {error}=await ctx.supabaseAdmin.rpc('reda_activate_plan_internal',{p_plan_id:planId,p_actor_id:actorId})
    if(error) return Response.json({error:'Plan activation failed'},{status:400})
    return Response.json({ok:true})
  })
}
