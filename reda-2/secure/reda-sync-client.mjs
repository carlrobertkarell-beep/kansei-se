import { createClient } from '@supabase/supabase-js'

export function createRedaClient(url,publishableKey){
  if(!/^https:\/\//.test(url)||!String(publishableKey).startsWith('sb_publishable_')) throw new Error('Reda backend config missing')
  const db=createClient(url,publishableKey,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}})
  async function requireClinician(){
    const [{data:{user}},{data:aal}]=await Promise.all([db.auth.getUser(),db.auth.mfa.getAuthenticatorAssuranceLevel()])
    if(!user||aal?.currentLevel!=='aal2') throw new Error('Clinician MFA required')
    const {data,error}=await db.from('reda_profiles').select('role,display_name').eq('user_id',user.id).single();if(error||data?.role!=='clinician')throw new Error('Clinician access required');return user
  }
  return {
    db,
    async clinicianDashboard(){await requireClinician();const {data:patients,error}=await db.from('reda_patients').select('id,display_name,status,updated_at').eq('status','active').order('updated_at',{ascending:false});if(error)throw error;return patients},
    async createPatient(displayName){const user=await requireClinician();const {data,error}=await db.from('reda_patients').insert({clinician_id:user.id,display_name:String(displayName).trim()}).select('id,display_name').single();if(error)throw error;return data},
    async createDraft(patientId,payload){const user=await requireClinician();const {data:last}=await db.from('reda_plans').select('version').eq('patient_id',patientId).order('version',{ascending:false}).limit(1);const version=(last?.[0]?.version||0)+1;const {data,error}=await db.from('reda_plans').insert({patient_id:patientId,clinician_id:user.id,version,status:'draft',payload}).select('id,version').single();if(error)throw error;return data},
    async activatePlan(planId){await requireClinician();const {error}=await db.rpc('reda_activate_plan',{p_plan_id:planId});if(error)throw error},
    async invitePatient(patientId,email){await requireClinician();const {data,error}=await db.functions.invoke('invite-patient',{body:{patient_id:patientId,email}});if(error)throw error;return data},
    async patientBootstrap(){const {data:{user}}=await db.auth.getUser();if(!user)throw new Error('Sign in required');const {data:patient,error:pErr}=await db.from('reda_patients').select('id,display_name').eq('auth_user_id',user.id).single();if(pErr)throw pErr;const {data:plan,error}=await db.from('reda_plans').select('id,version,payload,activated_at').eq('patient_id',patient.id).eq('status','active').single();if(error)throw error;return {patient,plan}},
    async saveSession(planId,session){const args={p_client_session_id:session.clientSessionId,p_plan_id:planId,p_status:session.status,p_started_at:session.startedAt,p_completed_at:session.completedAt||null,p_payload:session.payload||{}};const {data,error}=await db.rpc('reda_save_session',args);if(error)throw error;return data},
    subscribeToPatientPlans(patientId,onChange){return db.channel('reda-plan-'+patientId).on('postgres_changes',{event:'*',schema:'public',table:'reda_plans',filter:'patient_id=eq.'+patientId},onChange).subscribe()}
  }
}
