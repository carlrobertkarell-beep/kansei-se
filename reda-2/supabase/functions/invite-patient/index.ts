import { withSupabase } from 'npm:@supabase/server@1.5.3'

export default {
  fetch: withSupabase({ auth: 'user' }, async (req, ctx) => {
    if (req.method !== 'POST') return Response.json({error:'Method not allowed'},{status:405})
    if (ctx.jwtClaims?.aal !== 'aal2') return Response.json({error:'MFA required'},{status:403})
    const { data: profile } = await ctx.supabase.from('reda_profiles').select('role').single()
    if (profile?.role !== 'clinician') return Response.json({error:'Clinician required'},{status:403})
    const body = await req.json().catch(()=>null)
    const patientId = body?.patient_id, email = String(body?.email||'').trim().toLowerCase()
    if (!patientId || !/^\S+@\S+\.\S+$/.test(email)) return Response.json({error:'Invalid request'},{status:400})
    const { data: patient, error: patientError } = await ctx.supabase.from('reda_patients').select('id,auth_user_id').eq('id',patientId).single()
    if (patientError || !patient) return Response.json({error:'Patient not found'},{status:404})
    if (patient.auth_user_id) return Response.json({error:'Patient already linked'},{status:409})
    const redirectTo = Deno.env.get('REDA_PATIENT_REDIRECT')
    if (!redirectTo) return Response.json({error:'Server not configured'},{status:503})
    const { data: invited, error: inviteError } = await ctx.supabaseAdmin.auth.admin.inviteUserByEmail(email,{redirectTo})
    if (inviteError || !invited.user) return Response.json({error:'Invitation failed'},{status:400})
    const { error: linkError } = await ctx.supabaseAdmin.from('reda_patients').update({auth_user_id:invited.user.id,updated_at:new Date().toISOString()}).eq('id',patient.id)
    if (linkError) return Response.json({error:'Account linking failed'},{status:500})
    await ctx.supabaseAdmin.from('reda_profiles').upsert({user_id:invited.user.id,role:'patient',display_name:''})
    await ctx.supabaseAdmin.from('reda_audit_events').insert({actor_id:ctx.userClaims?.id,patient_id:patient.id,action:'patient_invited',metadata:{}})
    return Response.json({ok:true})
  })
}
