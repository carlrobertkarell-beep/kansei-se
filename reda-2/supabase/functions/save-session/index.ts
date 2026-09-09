import { withSupabase } from 'npm:@supabase/server@1.5.3'

export default {
  fetch: withSupabase({ auth: 'user' }, async (req, ctx) => {
    if (req.method !== 'POST') return Response.json({error:'Method not allowed'},{status:405})
    const userId=ctx.userClaims?.id
    if(!userId) return Response.json({error:'Sign in required'},{status:401})
    const body=await req.json().catch(()=>null)
    if(!body?.client_session_id||!body?.plan_id||!['started','partial','completed','planned_rest'].includes(body?.status)) return Response.json({error:'Invalid request'},{status:400})
    const {data,error}=await ctx.supabaseAdmin.rpc('reda_save_session_internal',{
      p_user_id:userId,p_client_session_id:body.client_session_id,p_plan_id:body.plan_id,p_status:body.status,
      p_started_at:body.started_at,p_completed_at:body.completed_at||null,p_payload:body.payload||{}
    })
    if(error) return Response.json({error:'Session sync failed'},{status:400})
    return Response.json({ok:true,id:data})
  })
}
